"""Approximation Ratio metric for evaluating solution quality against optimal solutions."""

from luna_model import Sense, Solution
from pydantic import Field

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature
from luna_bench.components.helper.divider_helper import get_ratio
from luna_bench.helpers import metric
from luna_bench.types import MetricResult


class ApproximationRatioResult(MetricResult):
    """Result container for the Approximation Ratio metric.

    Attributes
    ----------
    approximation_ratio : float
        The calculated approximation ratio. A value of 1.0 indicates an optimal
        solution. For minimization as for maximization problems, values > 1 indicate worse solutions quality.
        Returns inf if no solution was found.
    """

    approximation_ratio: float = Field(ge=1.0, description="The calculated approximation ratio.")


@metric(required_features=OptSolFeature)
class ApproximationRatio(BaseMetric[ApproximationRatioResult]):
    """Metric that calculates the approximation ratio of a solution against the optimal.

    The approximation ratio measures how close a found expectation value of a given solution
    is to the optimal solution. It uses the expectation value (average energy) of
    all samples in the solution rather than just the best sample. A value of 1.0 indicates an optimal
    solution, while values > 1.0 indicate progressively worse solution quality.


    For minimization problems:
        AR = expectation_value / optimal_value

    For maximization problems:
        AR = optimal_value / expectation_value

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

    def run(self, solution: Solution, feature_results: FeatureResults) -> ApproximationRatioResult:
        """Calculate the approximation ratio for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run with a given model.
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
        ZeroDivisionError
            If the denominator (optimal value for Min, expectation value for Max)
            is close to zero (within abt_diff tolerance).
        """
        # Get the optimal solution from features
        opt_sol = feature_results.first(feature_cls=OptSolFeature)

        # Check if any solution exists
        if len(solution.samples) == 0:
            return ApproximationRatioResult(approximation_ratio=float("inf"))

        exp_val = solution.expectation_value()

        # Calculate ratio based on optimization sense
        nom, denom = (exp_val, opt_sol.best_sol) if solution.sense == Sense.MIN else (opt_sol.best_sol, exp_val)
        ar = get_ratio(nominator=nom, denominator=denom, abt_diff=self.abt_diff)

        return ApproximationRatioResult(approximation_ratio=ar)
