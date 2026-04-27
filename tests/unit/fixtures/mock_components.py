from __future__ import annotations

from typing import TYPE_CHECKING

from luna_model import Solution
from pydantic import BaseModel
from returns.result import Result, Success

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.helpers.decorators import algorithm, feature, metric, plot
from luna_bench.types import MetricResult

if TYPE_CHECKING:
    from luna_model import Model

    from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
    from luna_bench.base_components.data_types.feature_results import FeatureResults


@feature(feature_id="mock_feature")
class MockFeature(BaseFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        return ArbitraryDataDomain.model_construct(solution="xD")  # type: ignore[call-arg] # Fake data


@feature
class MockFeatureFailing(BaseFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        raise ValueError("Model failed.")  # noqa: TRY003 # Just simulating a random error


class UnregisteredFeature(BaseFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:
        raise NotImplementedError


@algorithm
class MockAlgorithm(BaseAlgorithmSync):
    def run(self, model: Model) -> Solution:
        raise NotImplementedError


class AsyncReturnData(BaseModel):
    model_name: str


@algorithm
class MockAsyncAlgorithm(BaseAlgorithmAsync[AsyncReturnData]):
    @property
    def model_type(self) -> type[AsyncReturnData]:
        return AsyncReturnData

    def run_async(self, model: Model) -> AsyncReturnData:
        return AsyncReturnData.model_construct(model_name=model.name)

    def fetch_result(self, model: Model, retrieval_data: AsyncReturnData) -> Result[Solution, str]:  # noqa: ARG002
        return Success(Solution([]))


class UnregisteredAlgorithm(BaseAlgorithmSync):
    def run(self, model: Model) -> Solution:
        raise NotImplementedError


@plot
class MockPlot(BasePlot):
    def run(self, benchmark_results: BenchmarkResults) -> None:
        raise NotImplementedError


class UnregisteredPlot(BasePlot):
    def run(self, benchmark_results: BenchmarkResults) -> None:
        raise NotImplementedError


@plot
class MockPlotWithError(BasePlot):
    def run(self, benchmark_results: BenchmarkResults) -> None:
        raise NotImplementedError


@metric(metric_id="mock_metric")
class MockMetric(BaseMetric):
    def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:  # noqa: ARG002
        return MetricResult()


@metric
class MockMetricError(BaseMetric):
    def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:
        raise NotImplementedError


class UnregisteredMetric(BaseMetric):
    def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:  # noqa: ARG002
        return MetricResult()
