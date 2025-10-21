from typing import Protocol

from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.result import Result

from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel, MetricUserModel, PlotUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BenchmarkCreateUc(Protocol):
    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError]: ...


class BenchmarkDeleteUc(Protocol):
    def __call__(self, benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class BenchmarkLoadUc(Protocol):
    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkUserModel, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError]: ...


class BenchmarkLoadAllUc(Protocol):
    def __call__(
        self,
    ) -> Result[list[BenchmarkUserModel], UnknownLunaBenchError | UnknownIdError | ValidationError]: ...


class MetricAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, metric: IMetric
    ) -> Result[
        MetricUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class FeatureAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, feature: IFeature
    ) -> Result[
        FeatureUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class FeatureRunUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel, feature: FeatureUserModel | None = None
    ) -> Result[None, RunFeatureMissingError | RunModelsetMissingError]: ...


class PlotAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, plot: IPlot
    ) -> Result[
        PlotUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class AlgorithmAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, algorithm: IAlgorithm[IBackend]
    ) -> Result[
        AlgorithmUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class MetricRemoveUc(Protocol):
    def __call__(
        self, benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class FeatureRemoveUc(Protocol):
    def __call__(
        self, benchmark_name: str, feature_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class BenchmarkRemoveModelsetUc(Protocol):
    def __call__(self, benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class PlotRemoveUc(Protocol):
    def __call__(
        self, benchmark_name: str, plot_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class AlgorithmRemoveUc(Protocol):
    def __call__(
        self, benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class BenchmarkSetModelsetUc(Protocol):
    def __call__(
        self, benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class PlotsRunUc(Protocol):
    error_handling_mode: UseCaseErrorHandlingMode

    def __call__(self, benchmark: BenchmarkUserModel) -> Result[None, PlotRunError | UnknownLunaBenchError]: ...
