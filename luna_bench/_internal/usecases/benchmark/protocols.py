from typing import Any, Protocol

from luna_quantum import Solution
from pydantic import BaseModel, ValidationError
from returns.maybe import Maybe
from returns.result import Result

from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench._internal.user_models import (
    AlgorithmUserModel,
    BenchmarkUserModel,
    MetricUserModel,
    ModelMetadataUserModel,
    PlotUserModel,
)
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
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
        self, benchmark_name: str, name: str, metric: BaseMetric
    ) -> Result[
        MetricUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class MetricRunUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel, metric: MetricUserModel | None = None
    ) -> Result[None, RunMetricMissingError | RunModelsetMissingError]: ...


class FeatureAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, feature: BaseFeature
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
        self, benchmark_name: str, name: str, plot: BasePlot[Any]
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
        self, benchmark_name: str, name: str, algorithm: BaseAlgorithmSync | BaseAlgorithmAsync[Any]
    ) -> Result[
        AlgorithmUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class AlgorithmRunUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel, algorithm: AlgorithmUserModel | None = None
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError]: ...


class AlgorithmFilterUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel, algorithm_type: AlgorithmType, algorithm: AlgorithmUserModel | None = None
    ) -> Result[list[AlgorithmUserModel], RunAlgorithmMissingError]: ...


class AlgorithmRunAsBackgroundTasksUc(Protocol):
    def __call__(
        self,
        benchmark_name: str,
        models: list[ModelMetadataUserModel],
        algorithms: list[AlgorithmUserModel],
    ) -> None: ...


class AlgorithmRetrieveAsyncRetrivalDataUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]: ...


class AlgorithmRetrieveAsyncSolutionsUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel
    ) -> Result[
        None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError
    ]: ...


class AlgorithmRetrieveSyncSolutionsUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkUserModel
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]: ...


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

    def __call__(
        self,
        benchmark: BenchmarkUserModel,
        error_handling_mode: UseCaseErrorHandlingMode = UseCaseErrorHandlingMode.FAIL_ON_ERROR,
    ) -> Result[None, PlotRunError | UnknownLunaBenchError]: ...


class BackgroundRunAlgorithmAsyncUc(Protocol):
    def __call__(self, algorithm: BaseAlgorithmAsync[Any], model_id: int) -> str: ...


class BackgroundRunAlgorithmSyncUc(Protocol):
    def __call__(self, algorithm: BaseAlgorithmSync, model_id: int) -> str: ...


class BackgroundRetrieveAlgorithmAsyncUc(Protocol):
    def __call__(
        self, task_id: str
    ) -> Maybe[
        Result[BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]: ...


class BackgroundRetrieveAlgorithmSyncUc(Protocol):
    def __call__(
        self, task_id: str
    ) -> Maybe[
        Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]: ...
