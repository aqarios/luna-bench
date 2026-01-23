from typing import Any, Protocol

from luna_quantum import Solution
from pydantic import BaseModel, ValidationError
from returns.maybe import Maybe
from returns.result import Result

from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    MetricEntity,
    ModelMetadataEntity,
    PlotEntity,
)
from luna_bench.entities.feature_entity import FeatureEntity
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
    ) -> Result[BenchmarkEntity, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError]: ...


class BenchmarkDeleteUc(Protocol):
    def __call__(self, benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class BenchmarkLoadUc(Protocol):
    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkEntity, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError]: ...


class BenchmarkLoadAllUc(Protocol):
    def __call__(
        self,
    ) -> Result[list[BenchmarkEntity], UnknownLunaBenchError | UnknownIdError | ValidationError]: ...


class MetricAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, metric: BaseMetric
    ) -> Result[
        MetricEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class MetricRunUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity, metric: MetricEntity | None = None
    ) -> Result[None, RunMetricMissingError | RunModelsetMissingError | RunFeatureMissingError]: ...


class FeatureAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, feature: BaseFeature
    ) -> Result[
        FeatureEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class FeatureRunUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity, feature: FeatureEntity | None = None
    ) -> Result[None, RunFeatureMissingError | RunModelsetMissingError]: ...


class PlotAddUc(Protocol):
    def __call__(
        self, benchmark_name: str, name: str, plot: BasePlot[Any]
    ) -> Result[
        PlotEntity,
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
        AlgorithmEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]: ...


class AlgorithmRunUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity, algorithm: AlgorithmEntity | None = None
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError]: ...


class AlgorithmFilterUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity, algorithm_type: AlgorithmType, algorithm: AlgorithmEntity | None = None
    ) -> Result[list[AlgorithmEntity], RunAlgorithmMissingError]: ...


class AlgorithmRunAsBackgroundTasksUc(Protocol):
    def __call__(
        self,
        benchmark_name: str,
        models: list[ModelMetadataEntity],
        algorithms: list[AlgorithmEntity],
    ) -> None: ...


class AlgorithmRetrieveAsyncRetrivalDataUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]: ...


class AlgorithmRetrieveAsyncSolutionsUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[
        None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError
    ]: ...


class AlgorithmRetrieveSyncSolutionsUc(Protocol):
    def __call__(
        self, benchmark: BenchmarkEntity
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
        benchmark: BenchmarkEntity,
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
