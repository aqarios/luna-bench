"""Runtime metric for measuring solution computation time."""

from luna_model import Solution, Timing
from pydantic import Field

from luna_bench.custom import BaseMetric, metric
from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class RuntimeResult(MetricResult):
    """Result container for the Runtime metric.

    Attributes
    ----------
    runtime_seconds : float
        The total runtime in seconds for computing the solution.
    """

    runtime_seconds: float = Field(ge=0.0, description="The total runtime in seconds for computing the solution.")


@metric
class Runtime(BaseMetric[RuntimeResult]):
    """Metric that captures the total runtime of a solution computation.

    This metric provides a simple way to track and compare the computational
    time required by different algorithms to produce their solutions.

    Examples
    --------
    >>> from luna_bench.components.metrics.runtime import Runtime
    >>> metric = Runtime()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Runtime: {result.runtime_seconds} seconds")
    """

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> RuntimeResult:  # noqa: ARG002
        """Retrieve the runtime from the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing runtime information.
        feature_results : FeatureResultContainer
            Container with pre-computed feature results (not used by this metric).

        Returns
        -------
        RuntimeResult
            Contains the total runtime in seconds.
        """
        match solution.runtime:
            case None:
                return RuntimeResult(runtime_seconds=float("inf"))
            case Timing():
                return RuntimeResult(runtime_seconds=solution.runtime.total_seconds)
