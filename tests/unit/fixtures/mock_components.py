from typing import Any

from luna_quantum import Model
from luna_quantum.solve import SolveJob
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.helpers.decorators import algorithm, feature, metric, plot


@feature
class MockFeature(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        return ArbitraryDataDomain.model_construct(solution="xD")  # type: ignore[call-arg] # Fake data


@feature
class MockFeatureFailing(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        raise ValueError("Model failed.")  # noqa: TRY003 # Just simulating a random error


class UnregisteredFeature(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:
        raise NotImplementedError


@algorithm
class MockAlgorithm(IAlgorithm[IBackend]):
    def run(
        self,
        model: Model | str,
        name: str | None = None,
        backend: IBackend | None = None,
        *args: Any | None,
        **kwargs: Any | None,
    ) -> SolveJob:
        raise NotImplementedError


class UnregisteredAlgorithm(IAlgorithm[IBackend]):
    def run(
        self,
        model: Model | str,
        name: str | None = None,
        backend: IBackend | None = None,
        *args: Any | None,
        **kwargs: Any | None,
    ) -> SolveJob:
        raise NotImplementedError


@plot
class MockPlot(IPlot):
    def run(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def validate_plot(self, benchmark: BenchmarkUserModel) -> Result[None, PlotRunError | UnknownLunaBenchError]:  # noqa: ARG002
        return Success(None)


class UnregisteredPlot(IPlot):
    def run(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def validate_plot(self, benchmark: BenchmarkUserModel) -> Result[None, PlotRunError | UnknownLunaBenchError]:
        raise NotImplementedError


@plot
class MockPlotWithValidationError(IPlot):
    def run(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def validate_plot(self, benchmark: BenchmarkUserModel) -> Result[None, PlotRunError | UnknownLunaBenchError]:  # noqa: ARG002
        return Failure(PlotRunError())


@metric
class MockMetric(IMetric):
    def run(self) -> None:
        raise NotImplementedError


class UnregisteredMetric(IMetric):
    def run(self) -> None:
        raise NotImplementedError
