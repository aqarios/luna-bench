from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

from luna_bench._internal.domain_models.metric_config_domain import MetricConfigDomain
from luna_bench._internal.domain_models.modelmetric_config_domain import ModelmetricConfigDomain

if TYPE_CHECKING:
    from types import TracebackType

    from pydantic import BaseModel
    from returns.result import Result

    from luna_bench._internal.domain_models import (
        AlgorithmConfigDomain,
        AlgorithmResultDomain,
        BenchmarkDomain,
        BenchmarkStatus,
        ModelMetadataDomain,
        ModelSetDomain,
        PlotConfigDomain,
    )
    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class DaoTransaction(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    @property
    def modelset(self) -> ModelSetDao: ...

    @property
    def model(self) -> ModelDao: ...

    @property
    def benchmark(self) -> BenchmarkDao: ...

    @property
    def model_metric(self) -> ModelmetricDao: ...

    @property
    def metric(self) -> MetricDao: ...

    @property
    def algorithm(self) -> AlgorithmDao: ...

    @property
    def plot(self) -> PlotDao: ...


class ModelDao(Protocol):
    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]: ...

    @staticmethod
    def get_or_create(
        model_name: str, model_hash: int, binary: bytes
    ) -> Result[ModelMetadataDomain, UnknownLunaBenchError]: ...

    @staticmethod
    def load(model_id: int) -> Result[bytes, DataNotExistError | UnknownLunaBenchError]: ...


class PlotDao(Protocol):
    @staticmethod
    def add(
        benchmark_name: str, plot_name: str, plot_config: PlotConfigDomain.PlotConfig
    ) -> Result[PlotConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove(benchmark_name: str, plot_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update(
        benchmark_name: str, plot_name: str, plot_config: PlotConfigDomain.PlotConfig
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_status(
        benchmark_name: str, plot_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, plot_name: str
    ) -> Result[PlotConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...


class ModelmetricDao(Protocol):
    @staticmethod
    def add(
        benchmark_name: str, modelmetric_name: str, modelmetric_config: ModelmetricConfigDomain.ModelmetricConfig
    ) -> Result[ModelmetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove(
        benchmark_name: str, modelmetric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update(
        benchmark_name: str, modelmetric_name: str, modelmetric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_status(
        benchmark_name: str, modelmetric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def set_result(
        benchmark_name: str, modelmetric_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_result(
        benchmark_name: str, modelmetric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, metric_name: str
    ) -> Result[ModelmetricConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...


class MetricDao(Protocol):
    @staticmethod
    def add(
        benchmark_name: str, metric_name: str, metric_config: MetricConfigDomain.MetricConfig
    ) -> Result[MetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update(
        benchmark_name: str, metric_name: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_status(
        benchmark_name: str, metric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def set_result(
        benchmark_name: str, metric_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_result(
        benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, metric_name: str
    ) -> Result[MetricConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...


class AlgorithmDao(Protocol):
    @staticmethod
    def add(
        benchmark_name: str,
        solvejob_name: str,
        algorithm: AlgorithmConfigDomain.Algorithm,
        backend: AlgorithmConfigDomain.Backend | None = None,
    ) -> Result[AlgorithmConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove(benchmark_name: str, solvejob_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update(
        benchmark_name: str,
        solvejob_name: str,
        algorithm: AlgorithmConfigDomain.Algorithm,
        backend: AlgorithmConfigDomain.Backend | None = None,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def update_status(
        benchmark_name: str, solvejob_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def load(
        benchmark_name: str, solvejob_name: str
    ) -> Result[AlgorithmConfigDomain, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def set_result(
        benchmark_name: str, solvejob_name: str, result: AlgorithmResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...

    @staticmethod
    def remove_result(
        benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]: ...


class BenchmarkDao(Protocol):
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


class ModelSetDao(Protocol):
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
