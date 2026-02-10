"""Time to Solution metric for evaluating solver efficiency.

Metric implemented from https://arxiv.org/pdf/2405.07624
"""

import numpy as np
from luna_quantum import Solution
from pydantic import Field

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature, OptSolFeatureResult
from luna_bench.helpers import metric
from luna_bench.types import MetricResult


class TimeToSolutionResult(MetricResult):
    """Result container for the Time to Solution metric.

    Attributes
    ----------
    time_to_solution : float
        The estimated time required to find the optimal solution with 99% probability.
        Returns inf if no optimal solutions were found in the samples.
    probability_optimal : float
        The probability of finding the optimal solution in a single sample.
    num_optimal_found : int
        The number of samples that found the optimal solution.
    num_samples : int
        The total number of samples in the solution.
    """

    time_to_solution: float = Field(ge=0.0, description="The estimated time required to find the optimal solution.")
    probability_optimal: float = Field(ge=0.0, le=1.0, description="The probability of finding the optimal solution.")
    num_optimal_found: int = Field(ge=0, description="The number of samples that found the optimal solution.")
    num_samples: int = Field(ge=0, description="The total number of samples in the solution.")


@metric(required_features=OptSolFeature)
class TimeToSolution(BaseMetric):
    r"""Metric that calculates the Time-to-Solution (TTS) for finding optimal solutions.

    The Time-to-Solution metric measures how long it takes for a solver to find
    the optimal solution with a high probability (99%). This metric is particularly
    useful for comparing heuristic solvers and quantum optimization algorithms.

    For heuristic solvers, TTS is calculated based on the probability of finding
    the optimal solution within a set of samples:

    .. math::

        \text{TTS}(X) = \left( \frac{t_{\text{solve}}}{M} \right)
        \left( \lceil \frac{\log(1 - 0.99)}{\log(1 - p^*)} \rceil \right)

    Where:
    - :math:`t_{\text{solve}}` is the total time taken to solve the problem,
    - :math:`M` is the number of samples,
    - :math:`p^*` is the probability of measuring the optimal solution.

    Special cases:
    - If :math:`p^* = 0` (no optimal solutions found): TTS = infinity
    - If :math:`p^* = 1` (all solutions optimal): TTS = time per sample

    Attributes
    ----------
    target_probability : float
        The target probability of finding the optimal solution. Default is 0.99.
    abs_tol : float
        Absolute tolerance for comparing objective values. Default is 1e-6.

    Examples
    --------
    >>> from luna_bench.components.metrics.time_to_solution import TimeToSolution
    >>> metric = TimeToSolution()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"TTS: {result.time_to_solution} seconds")
    >>> print(f"Probability of optimal: {result.probability_optimal}")

    Notes
    -----
    This metric requires the OptSolFeature to be computed first, which provides
    the optimal solution value for comparison.

    **Source**: https://arxiv.org/pdf/2405.07624
    """

    target_probability: float = 0.99
    abs_tol: float = 1e-6

    def run(self, solution: Solution, feature_results: FeatureResults) -> TimeToSolutionResult:
        """Calculate the Time-to-Solution for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
        feature_results : FeatureResults
            Container with pre-computed feature results. Must include results
            from OptSolFeature which provides the optimal solution value.

        Returns
        -------
        TimeToSolutionResult
            Contains the calculated TTS and related statistics.
        """
        # Get the optimal solution from features
        opt_sol: OptSolFeatureResult
        (opt_sol, _) = feature_results.first(feature_cls=OptSolFeature)  # type: ignore[assignment]
        optimum = opt_sol.best_sol

        # Check if any solution exists
        num_samples = solution.counts.sum()
        if num_samples == 0:
            return TimeToSolutionResult(
                time_to_solution=float("inf"),
                probability_optimal=0.0,
                num_optimal_found=0,
                num_samples=0,
            )

        # Count optimal solutions using results (which have obj_value)
        filt_sol = solution.filter_feasible().filter(
            lambda s: s.obj_value is not None and bool(np.isclose(s.obj_value, optimum, atol=self.abs_tol))
        )
        num_optimal_found = filt_sol.counts.sum()

        # Calculate the probability of finding optimal
        p_star = float(num_optimal_found / num_samples)

        # Calculate time per sample
        if solution.runtime is None:
            raise ValueError
        total_runtime = solution.runtime.total_seconds
        t_per_sample = total_runtime / num_samples

        # Calculate TTS
        tts: float
        if p_star == 0.0:
            tts = float("inf")
        elif p_star == 1.0:
            tts = t_per_sample
        else:
            num_repetitions = np.ceil(np.log(1 - self.target_probability) / np.log(1 - p_star))
            tts = t_per_sample * num_repetitions

        return TimeToSolutionResult(
            time_to_solution=tts,
            probability_optimal=p_star,
            num_optimal_found=num_optimal_found,
            num_samples=num_samples,
        )
