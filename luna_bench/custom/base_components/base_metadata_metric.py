"""A metric that is handed the metadata of the run it evaluates.

``BaseMetric.run`` takes the solution and the feature results, and that is the whole contract:
a metric reports on the solution, not on how it was produced. Solver metadata is the other
half - queue time, device, shot count - and a metric that reports on it needs one more
argument.

It arrives through a subclass rather than through a third parameter on ``BaseMetric.run``,
because widening that signature would break the override in the other direction: a metric
that takes two arguments is no longer a valid override of a base that takes three, so every
existing metric, built-in or user-written, would have to change to accommodate a parameter it
never reads. Opting in leaves them all alone.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from luna_model import Solution

from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.result_containers.solve_metadata import SolveMetadata

from .base_metric import BaseMetric

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class BaseMetadataMetric[TMetricResult: MetricResult = MetricResult](BaseMetric[TMetricResult], ABC):
    """
    Base class for metrics that read the metadata of the run they evaluate.

    Implement ``run_with_metadata`` instead of ``run``. A benchmark run hands over the metadata
    the algorithm reported for that one ``(model, algorithm)`` pair; reading the content of
    metadata that was never reported raises ``MetadataNotAvailableError``, which the benchmark
    records as a failed metric result for that pair alone.

    Examples
    --------
    >>> @metric()
    ... class DeviceRuntime(BaseMetadataMetric[DeviceRuntimeResult]):
    ...     def run_with_metadata(
    ...         self,
    ...         solution: Solution,
    ...         feature_results: FeatureResultContainer,
    ...         metadata: SolveMetadata,
    ...     ) -> DeviceRuntimeResult:
    ...         return DeviceRuntimeResult(runtime=metadata["device_runtime"])
    """

    def run(self, solution: Solution, feature_results: "FeatureResultContainer") -> TMetricResult:
        """
        Compute the metric value without any metadata.

        Reached when the metric is called outside a benchmark run, which is the one place that
        knows which run is being evaluated. Every read of the empty metadata raises.

        Parameters
        ----------
        solution: Solution
            The solution for which the metric should be computed.
        feature_results: FeatureResultContainer
            The results of the features this metric declared.

        Returns
        -------
        TMetricResult
            The result of the computed metric.
        """
        return self.run_with_metadata(solution, feature_results, SolveMetadata())

    @abstractmethod
    def run_with_metadata(
        self,
        solution: Solution,
        feature_results: "FeatureResultContainer",
        metadata: SolveMetadata,
    ) -> TMetricResult:
        """
        Compute the metric value for a given solution and the metadata of its run.

        Parameters
        ----------
        solution: Solution
            The solution for which the metric should be computed.
        feature_results: FeatureResultContainer
            If the metric requires additional features so it can be calculated, they will be provided here.
        metadata: SolveMetadata
            What the algorithm reported about the run that produced *solution*.

        Returns
        -------
        TMetricResult
            The result of the computed metric.
        """
