"""Best Solution Found metric for evaluating solution quality against optimal solutions.

Metric implemented from https://arxiv.org/pdf/2405.07624
"""

import numpy as np
from luna_quantum import Sense, Solution
from pydantic import field_validator

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature, OptSolFeatureResult
from luna_bench.helpers import metric
from luna_bench.types import MetricResult


class BestSolutionFoundError(ValueError):
    """Raised when best solution found validation fails.

    The best solution found ratio must be >= 1.0 by definition of metric.
    A value of 1.0 indicates an optimal solution was found, while values > 1.0
    indicate progressively worse solution quality.
    """

    def __init__(self) -> None:
        """Initialize BestSolutionFoundError with standard message."""
        msg = "Best Solution Found ratio must be >= 1.0 by definition of metric."
        super().__init__(msg)


class BestSolutionFoundResult(MetricResult):
    """Result container for the Best Solution Found metric.

    Attributes
    ----------
    best_solution_found : float
        The calculated best solution found ratio. A value of 1.0 indicates the
        optimal solution was found. For both minimization and maximization problems,
        values > 1.0 indicate worse solution quality.
        Returns inf if no solution was found.
    """

    best_solution_found: float

    @field_validator("best_solution_found")
    @classmethod
    def validate_best_solution_found(cls, v: float) -> float:
        """Validate the best solution found value.

        Parameters
        ----------
        v : float
            The best solution found ratio value to validate.

        Returns
        -------
        float
            The validated best solution found ratio.

        Raises
        ------
        ValueError
            If best solution found ratio is less than 1.0.
        """
        if v < 1.0:
            raise BestSolutionFoundError
        return v


@metric(required_features=OptSolFeature)
class BestSolutionFound(BaseMetric):
    r"""Metric that calculates the Best Solution Found (BSF) ratio against the optimal.

    The Best Solution Found metric measures how close the best sample in a solution
    is to the optimal solution. Unlike the Approximation Ratio which uses the
    expectation value (average energy), this metric uses only the best sample found.

    The relative cost :math:`c(X)` of the BSF in comparison to the optimal solution is:

    .. math::

        c(X) = \frac{\min_{x \in X} C(x)}{C(x^*)}

    Where:
    - :math:`C(x)` is the objective value of solution :math:`x`,
    - :math:`C(x^*)` is the objective value of the optimal solution :math:`x^*`,
    - :math:`\min_{x \in X} C(x)` represents the best solution found in sample set :math:`X`.

    For minimization problems:
        BSF = best_found_value / optimal_value
        - BSF = 1.0 means the best sample equals optimal
        - BSF > 1.0 means the best sample is worse than optimal

    For maximization problems:
        BSF = optimal_value / best_found_value
        - BSF = 1.0 means the best sample equals optimal
        - BSF > 1.0 means the best sample is worse than optimal

    Attributes
    ----------
    abs_tol : float
        Absolute tolerance for considering a value as zero. Used to prevent
        division by zero errors. Default is 1e-3.

    Examples
    --------
    >>> from luna_bench.components.metrics.best_solution_found import BestSolutionFound
    >>> metric = BestSolutionFound()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Best Solution Found ratio: {result.best_solution_found}")

    Notes
    -----
    This metric requires the OptSolFeature to be computed first, which provides
    the optimal solution value for comparison.

    **Source**: https://arxiv.org/pdf/2405.07624
    """

    abs_tol: float = 1e-3

    def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:
        """Calculate the Best Solution Found ratio for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
            Must have a valid sense (Min or Max) and provide best_sample().
        feature_results : FeatureResults
            Container with pre-computed feature results. Must include results
            from OptSolFeature which provides the optimal solution value.

        Returns
        -------
        BestSolutionFoundResult
            Contains the calculated BSF ratio. Returns inf if no
            solution samples are available.

        Raises
        ------
        NotImplementedError
            If the denominator (optimal value for Min, best found value for Max)
            is close to zero (within abs_tol tolerance).
        """
        bsf: float

        # Get the optimal solution from features
        opt_sol: OptSolFeatureResult
        (opt_sol, _) = feature_results.first(feature_cls=OptSolFeature)  # type: ignore[assignment]

        # Check if any solution exists
        if len(solution.samples) == 0:
            return BestSolutionFoundResult(best_solution_found=float("inf"))

        # Get the best objective value based on optimization sense
        if solution.sense == Sense.Min:
            best_value = float(min(solution.obj_values))
            bsf = self._get_ratio(numerator=best_value, denominator=opt_sol.best_sol)
        else:
            best_value = float(max(solution.obj_values))
            bsf = self._get_ratio(numerator=opt_sol.best_sol, denominator=best_value)

        return BestSolutionFoundResult(best_solution_found=bsf)

    def _get_ratio(self, numerator: float, denominator: float) -> float:
        """Calculate the ratio of two values with zero-division protection.

        Parameters
        ----------
        numerator : float
            The numerator of the ratio.
        denominator : float
            The denominator of the ratio.

        Returns
        -------
        float
            The calculated ratio (numerator / denominator).

        Raises
        ------
        NotImplementedError
            If the denominator is close to zero (within abs_tol tolerance).
        """
        if np.isclose(denominator, 0, atol=self.abs_tol):
            raise NotImplementedError("Best Solution Found is not implemented for cases dividing by 0!")
        return numerator / denominator
