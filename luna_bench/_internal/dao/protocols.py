from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

from luna_bench._internal.domain_models.metric_config_domain import MetricConfigDomain
from luna_bench._internal.domain_models.modelmetric_config_domain import ModelmetricConfigDomain

if TYPE_CHECKING:
    from types import TracebackType

    from pydantic import BaseModel
    from returns.result import Result

    from luna_bench._internal.domain_models import (
        BenchmarkDomain,
        BenchmarkStatus,
        ModelMetadataDomain,
        ModelSetDomain,
        PlotConfigDomain,
    )
    from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
    from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class StorageTransaction(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    @property
    def modelset(self) -> ModelSetStorage: ...

    @property
    def model(self) -> ModelStorage: ...

    @property
    def benchmark(self) -> BenchmarkStorage: ...

    @property
    def model_metric(self) -> ModelmetricStorage: ...

    @property
    def metric(self) -> MetricStorage: ...

    @property
    def solve_job(self) -> SolveJobStorage: ...

    @property
    def plot(self) -> PlotStorage: ...


class ModelStorage(Protocol):
    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]: ...

    @staticmethod
    def get_or_create(
        model_name: str, model_hash: int, binary: bytes
    ) -> Result[ModelMetadataDomain, UnknownLunaBenchError]: ...

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, DataNotExistError | UnknownLunaBenchError]: ...


class PlotStorage(Protocol):
    @staticmethod
    def add_plot(
        benchmark_name: str, plot_name: str, plot_config: BaseModel
    ) -> Result[PlotConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_plot(benchmark_name: str, plot_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_plot(
        benchmark_name: str, plot_name: str, plot_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_plot_status(
        benchmark_name: str, plot_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, plot_name: str
    ) -> Result[PlotConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...


class ModelmetricStorage(Protocol):
    @staticmethod
    def add_modelmetric(
        benchmark_name: str, modelmetric_name: str, modelmetric_config: ModelmetricConfigDomain.ModelmetricConfig
    ) -> Result[ModelmetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_modelmetric(
        benchmark_name: str, modelmetric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_modelmetric(
        benchmark_name: str, modelmetric_name: str, modelmetric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_modelmetric_status(
        benchmark_name: str, modelmetric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def set_result_modelmetric(
        benchmark_name: str, modelmetric_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_result_modelmetric(
        benchmark_name: str, modelmetric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, metric_name: str
    ) -> Result[ModelmetricConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...


class MetricStorage(Protocol):
    @staticmethod
    def add_metric(
        benchmark_name: str, metric_name: str, metric_config: MetricConfigDomain.MetricConfig
    ) -> Result[MetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_metric(
        benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_metric(
        benchmark_name: str, metric_name: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_metric_status(
        benchmark_name: str, metric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def set_result_metric(
        benchmark_name: str, metric_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_result_metric(
        benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, metric_name: str
    ) -> Result[MetricConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...


class SolveJobStorage(Protocol):
    @staticmethod
    def add_solvejob(
        benchmark_name: str, solvejob_name: str, solvejob_config: BaseModel
    ) -> Result[None, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_solvejob(
        benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_solvejob(
        benchmark_name: str, solvejob_name: str, solvejob_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_solvejob_status(
        benchmark_name: str, solvejob_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def set_result_solvejob(
        benchmark_name: str, solvejob_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_result_solvejob(
        benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class BenchmarkStorage(Protocol):
    @staticmethod
    def create(benchmark_name: str) -> Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(benchmark_name: str) -> Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def delete(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load_all() -> Result[list[BenchmarkDomain], UnknownLunaBenchError]: ...

    @staticmethod
    def set_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_modelset(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class ModelSetStorage(Protocol):
    @staticmethod
    def create(modelset_name: str) -> Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(modelset_name: str) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def delete(modelset_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def add_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], UnknownLunaBenchError]: ...

    @staticmethod
    def load_all_models(
        modelset_name: str,
    ) -> Result[list[ModelMetadataDomain], DataNotExistError | UnknownLunaBenchError]: ...
