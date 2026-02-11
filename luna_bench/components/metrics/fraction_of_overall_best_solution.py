"""Fraction of Overall Best Solution metric for evaluating solution quality.

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


class FractionOfOverallBestSolutionResult(MetricResult):
    """Result container for the Fraction of Overall Best Solution metric.

    Attributes
    ----------
    fraction_of_overall_best_solution : float
        The fraction of samples that match the overall best solution.
        Value ranges from 0.0 (no samples match) to 1.0 (all samples match).
        Returns 0.0 if there are no feasible samples.
    """

    fraction_of_overall_best_solution: float = Field(
        ge=0.0,
        le=1.0,
        description="The fraction of samples that match the overall best solution.",
    )


@metric(required_features=OptSolFeature)
class FractionOfOverallBestSolution(BaseMetric):
    r"""Metric that calculates the Fraction of Overall Best Solution (FOB).

    This metric evaluates how often a solver finds the overall best solution.
    It calculates the fraction of samples where the solver's solution matches
    the best known solution.

    The Fraction of Overall Best solution found (FOB) is defined as:

    .. math::

        \text{FOB}({X_i}) = \frac{|\{i \mid \hat{c}(X_i) = 1, \forall i \in I\}|}{|I|}

    Where:
    - :math:`X_i` represents the sample set obtained for instance :math:`i`,
    - :math:`\hat{c}(X_i) = 1` indicates that the solution for instance :math:`i`
      is the best solution found for that instance,
    - :math:`I` is the set of all instances.

    This metric is beneficial for comparing solvers based on their ability to find
    the best solution for each instance. It provides insight into how effective a
    solver is at consistently finding the optimal solution.

    Attributes
    ----------
    abs_tol : float
        Absolute tolerance for considering two values as equal. Default is 1e-6.

    Examples
    --------
    >>> from luna_bench.components.metrics.fraction_of_overall_best_solution import (
    ...     FractionOfOverallBestSolution,
    ... )
    >>> metric = FractionOfOverallBestSolution()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"FOB: {result.fraction_of_overall_best_solution}")

    Notes
    -----
    This metric requires the OptSolFeature to be computed first, which provides
    the optimal solution value for comparison.

    **Source**: https://arxiv.org/pdf/2405.07624
    """

    abs_tol: float = 1e-6

    def run(self, solution: Solution, feature_results: FeatureResults) -> FractionOfOverallBestSolutionResult:
        """Calculate the Fraction of Overall Best Solution for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
        feature_results : FeatureResults
            Container with pre-computed feature results. Must include results
            from OptSolFeature which provides the optimal solution value.

        Returns
        -------
        FractionOfOverallBestSolutionResult
            Contains the calculated FOB ratio. Returns 0.0 if no feasible
            samples are available.
        """
        if solution is None or len(solution.samples) == 0:
            return FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=0.0)

        # Get the optimal solution from features
        opt_sol: OptSolFeatureResult
        (opt_sol, _) = feature_results.first(feature_cls=OptSolFeature)  # type: ignore[assignment]
        optimum = opt_sol.best_sol
        filtered_sol = solution.filter_feasible().filter(
            lambda s: s.obj_value is not None and bool(np.isclose(s.obj_value, optimum, atol=self.abs_tol))
        )
        num_optimal_found = filtered_sol.counts.sum()

        # Return fraction of all samples that are optimal and feasible
        fob = num_optimal_found / solution.counts.sum()
        return FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=fob)
