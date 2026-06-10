"""Approximation Ratio metric for evaluating solution quality against optimal solutions."""

from luna_model import Solution
from luna_model.solution import ValueSource
from pydantic import Field

from luna_bench.custom import BaseMetric, FeatureResultContainer, MetricResult, metric
from luna_bench.features import OptSolFeature
from luna_bench.helpers import get_ratio


class ApproximationRatioResult(MetricResult):
    """Result container for the Approximation Ratio metric.

    Attributes
    ----------
    approximation_ratio : float
        The calculated approximation ratio. A value of 1.0 indicates an optimal
        solution. For minimization as for maximization problems, values < 1.0 indicate worse
        solution quality. Returns -inf if no solution was found.
    """

    approximation_ratio: float = Field(le=1.0, description="The calculated approximation ratio.")


@metric(OptSolFeature)
class ApproximationRatio(BaseMetric[ApproximationRatioResult]):
    """Metric that calculates the approximation ratio of a solution against the optimal.

    The approximation ratio measures how close a found expectation value of a given solution
    is to the optimal solution. It uses the expectation value (average energy) of
    all samples in the solution rather than just the best sample. A value of 1.0 indicates an optimal
    solution, while values < 1.0 indicate progressively worse solution quality. The metric is
    bounded by 1.0.

    It is computed from the (absolute) relative energy error of the expectation value with respect
    to the optimal value. Taking the absolute value makes the metric sense-agnostic (the same formula
    applies to minimization and maximization) and keeps it monotonic for negative or mixed-sign
    optimal values, since the expectation value is normalized against the fixed ``|optimal_value|``:

        relative_energy_error = (expectation_value - optimal_value) / optimal_value
        AR = 1 - abs(relative_energy_error)

    Attributes
    ----------
    abt_diff : float
        Absolute tolerance for considering a value as zero. Used to prevent
        division by zero errors. Default is 1e-3.
    value_source : ValueSource
        The value_source defines if the objective values or the raw energies values form the algorithm should be used
        to calulate the approximation ratio. Default is ValueSource.OBJ.

    Examples
    --------
    >>> from luna_bench.metrics import ApproximationRatio
    >>> metric = ApproximationRatio()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Approximation Ratio: {result.approximation_ratio}")

    Notes
    -----
    This metric requires the OptSolFeature to be computed first, which provides
    the optimal solution value for comparison.
    """

    abt_diff: float = 1e-3
    value_source: ValueSource = ValueSource.OBJ

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> ApproximationRatioResult:
        """Calculate the approximation ratio for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run with a given model.
        feature_results : FeatureResultContainer
            Container with pre-computed feature results. Must include results
            from OptSolFeature which provides the optimal solution value.

        Returns
        -------
        ApproximationRatioResult
            Contains the calculated approximation ratio. Returns -inf if no
            solution samples are available.

        Raises
        ------
        ZeroDivisionError
            If the optimal value is close to zero (within abt_diff tolerance),
            since the relative energy error is normalized by the optimal value.
        """
        # Get the optimal solution from features
        opt_sol = feature_results.first(feature_cls=OptSolFeature)

        # Check if any solution exists
        if len(solution.samples) == 0:
            return ApproximationRatioResult(approximation_ratio=float("-inf"))

        exp_val = solution.expectation_value(value_toggle=self.value_source)

        # Relative energy error of the expectation value w.r.t. the optimal value. Normalizing against
        # the fixed |optimal_value| and taking the absolute value makes the metric sense-agnostic and
        # keeps it monotonic for negative or mixed-sign optima.
        try:
            relative_energy_error = get_ratio(
                nominator=(exp_val - opt_sol.global_best_sol),
                denominator=opt_sol.global_best_sol,
                abt_diff=self.abt_diff,
            )
        except Exception as e:
            if isinstance(e, ZeroDivisionError):
                msg = "Approximation ratio cannot be calculated since the optimal value is zero."
                raise ZeroDivisionError(msg) from e
            raise

        return ApproximationRatioResult(approximation_ratio=1 - abs(relative_energy_error))
