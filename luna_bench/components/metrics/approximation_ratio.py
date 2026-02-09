"""Approximation Ratio metric for evaluating solution quality against optimal solutions."""

import numpy as np
from luna_quantum import Sense, Solution
from pydantic import field_validator

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature, OptSolFeatureResult
from luna_bench.helpers import metric
from luna_bench.types import MetricResult


class ApproximationRatioError(ValueError):
    """Raised when approximation ratio validation fails.

    The approximation ratio must be >= 1.0 by definition of metric.
    A value of 1.0 indicates an optimal solution, while values > 1.0
    indicate progressively worse solution quality.
    """

    def __init__(self) -> None:
        """Initialize ApproximationRatioError with standard message."""
        msg = "Approximation Ratio must be >= 1.0 by definition of metric."
        super().__init__(msg)


class ApproximationRatioResult(MetricResult):
    """Result container for the Approximation Ratio metric.

    Attributes
    ----------
    approximation_ratio : float
        The calculated approximation ratio. A value of 1.0 indicates an optimal
        solution. For minimization as for maximization problems, values > 1 indicate worse solutions quality.
        Returns inf if no solution was found.
    """

    approximation_ratio: float

    @field_validator("approximation_ratio")
    @classmethod
    def validate_approximation_ratio(cls, v: float) -> float:
        """Validate the approximation ratio value.

        Parameters
        ----------
        v : float
            The approximation ratio value to validate.

        Returns
        -------
        float
            The validated approximation ratio.

        Raises
        ------
        ValueError
            If approximation ratio is less than 1.0.
        """
        if v < 1.0:
            raise ApproximationRatioError
        return v


@metric(required_features=OptSolFeature)
class ApproximationRatio(BaseMetric):
    """Metric that calculates the approximation ratio of a solution against the optimal.

    The approximation ratio measures how close a found expectation value of a given solution
    is to the optimal solution. It uses the expectation value (average energy) of
    all samples in the solution rather than just the best sample.

    For minimization problems:
        AR = expectation_value / optimal_value
        - AR = 1.0 means the average solution equals optimal
        - AR > 1.0 means the average solution is worse than optimal

    For maximization problems:
        AR = optimal_value / expectation_value
        - AR = 1.0 means the average solution equals optimal
        - AR > 1.0 means the average solution is worse than optimal

    Attributes
    ----------
    abt_diff : float
        Absolute tolerance for considering a value as zero. Used to prevent
        division by zero errors. Default is 1e-3.

    Examples
    --------
    >>> from luna_bench.components.metrics.approximation_ratio import ApproximationRatio
    >>> metric = ApproximationRatio()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Approximation Ratio: {result.approximation_ratio}")

    Notes
    -----
    This metric requires the OptSolFeature to be computed first, which provides
    the optimal solution value for comparison.
    """

    abt_diff: float = 1e-3

    def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:
        """Calculate the approximation ratio for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
            Must have a valid sense (Min or Max) and provide expectation_value().
        feature_results : FeatureResults
            Container with pre-computed feature results. Must include results
            from OptSolFeature which provides the optimal solution value.

        Returns
        -------
        ApproximationRatioResult
            Contains the calculated approximation ratio. Returns inf if no
            solution samples are available.

        Raises
        ------
        NotImplementedError
            If the denominator (optimal value for Min, expectation value for Max)
            is close to zero (within abt_diff tolerance).
        """
        ar: float

        # Get the optimal solution from features
        opt_sol: OptSolFeatureResult
        (opt_sol, _) = feature_results.first(feature_cls=OptSolFeature)  # type: ignore[assignment]

        # Check if any solution exists
        if len(solution.samples) == 0:
            return ApproximationRatioResult(approximation_ratio=float("inf"))

        exp_val = solution.expectation_value()

        # Calculate ratio based on optimization sense
        if solution.sense == Sense.Min:
            ar = self._get_ratio(nominator=exp_val, denominator=opt_sol.best_sol)
        else:
            ar = self._get_ratio(nominator=opt_sol.best_sol, denominator=exp_val)

        return ApproximationRatioResult(approximation_ratio=ar)

    def _get_ratio(self, nominator: float, denominator: float) -> float:
        """Calculate the ratio of two values with zero-division protection.

        Parameters
        ----------
        nominator : float
            The numerator of the ratio.
        denominator : float
            The denominator of the ratio.

        Returns
        -------
        float
            The calculated ratio (nominator / denominator).

        Raises
        ------
        NotImplementedError
            If the denominator is close to zero (within abt_diff tolerance).
        """
        if np.isclose(denominator, 0, atol=self.abt_diff):
            raise NotImplementedError("Approximation Ratio is not implemented for cases dividing by 0!")
        return nominator / denominator
