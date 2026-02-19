"""Feasibility Ratio metric for measuring the proportion of feasible solutions."""

from luna_quantum import Solution
from pydantic import Field

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.helpers import metric
from luna_bench.types import MetricResult


class FeasibilityRatioResult(MetricResult):
    """Result container for the Feasibility Ratio metric.

    Attributes
    ----------
    feasibility_ratio : float
        The ratio of feasible solutions to total solutions.
        Value ranges from 0.0 (no feasible solutions) to 1.0 (all solutions feasible).
        Returns 0.0 if there are no samples.
    """

    feasibility_ratio: float = Field(ge=0.0, le=1.0, description="The ratio of feasible solutions to total solutions.")


@metric
class FeasibilityRatio(BaseMetric):
    """Metric that calculates the ratio of feasible solutions.

    The Feasibility Ratio measures what proportion of the samples returned by
    a solver satisfy all constraints of the optimization problem. This is
    particularly important for constrained optimization problems where not
    all samples may be valid solutions.

    A feasibility ratio of 1.0 indicates all samples are feasible, while 0.0
    indicates none are feasible.

    Examples
    --------
    >>> from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio
    >>> metric = FeasibilityRatio()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Feasibility Ratio: {result.feasibility_ratio}")

    Notes
    -----
    This metric relies on the feasibility information stored in the Solution
    object, which is typically computed by the solver or model evaluation.
    """

    def run(self, solution: Solution, feature_results: FeatureResults) -> FeasibilityRatioResult:  # noqa: ARG002
        """Calculate the feasibility ratio for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
        feature_results : FeatureResults
            Container with pre-computed feature results (not used by this metric).

        Returns
        -------
        FeasibilityRatioResult
            Contains the calculated feasibility ratio.
        """
        if len(solution.samples) == 0:
            return FeasibilityRatioResult(feasibility_ratio=0.0)
        return FeasibilityRatioResult(feasibility_ratio=solution.feasibility_ratio())
