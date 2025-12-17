from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Model, Solution
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.base_components.data_types.arbitrary_data import ArbitraryData
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.helpers.decorators import algorithm, feature, metric, plot

if TYPE_CHECKING:
    from luna_quantum import Model

    from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
    from luna_bench.base_components.data_types.feature_results import FeatureResults
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


@feature(feature_id="mock_feature")  # type: ignore[arg-type]
class MockFeature(BaseFeature):  # type: ignore[misc]
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
        return Success(
            Solution._build(  # type: ignore[attr-defined]
                component_types=[],
                binary_cols=[],
                spin_cols=None,
                int_cols=None,
                real_cols=None,
                raw_energies=None,
                timing=None,
                counts=[],
            )
        )


class UnregisteredAlgorithm(BaseAlgorithmSync):
    def run(self, model: Model) -> Solution:
        raise NotImplementedError


@plot
class MockPlot(BasePlot[str]):
    def run(self, data: str) -> None:
        raise NotImplementedError

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,  # noqa: ARG002
    ) -> Result[str, PlotRunError | UnknownLunaBenchError]:
        return Success("test")


class UnregisteredPlot(BasePlot[str]):
    def run(self, data: str) -> None:
        raise NotImplementedError

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[str, PlotRunError | UnknownLunaBenchError]:
        raise NotImplementedError


@plot
class MockPlotWithValidationError(BasePlot[str]):
    def run(self, data: str) -> None:
        raise NotImplementedError

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,  # noqa: ARG002
    ) -> Result[str, PlotRunError | UnknownLunaBenchError]:
        return Failure(PlotRunError())


@metric(metric_id="mock_metric")  # type: ignore[arg-type]
class MockMetric(BaseMetric):  # type: ignore[misc]
    def run(self, solution: Solution, feature_results: FeatureResults) -> ArbitraryData:  # noqa: ARG002
        return ArbitraryData()


@metric
class MockMetricError(BaseMetric):
    def run(self, solution: Solution, feature_results: FeatureResults) -> ArbitraryData:
        raise NotImplementedError


class UnregisteredMetric(BaseMetric):
    def run(self, solution: Solution, feature_results: FeatureResults) -> ArbitraryData:  # noqa: ARG002
        return ArbitraryData()
