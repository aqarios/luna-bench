from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

from pydantic import BaseModel

if TYPE_CHECKING:
    from types import TracebackType

    from returns.result import Result

    from luna_bench._internal.domain_models import BenchmarkDomain, ModelMetadataDomain, ModelSetDomain
    from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
    from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class StorageTransaction(Protocol):
    def __enter__(self) -> Self:
        pass

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    @property
    def modelset(self) -> ModelSetStorage:
        pass

    @property
    def model(self) -> ModelStorage:
        pass

    @property
    def benchmark(self) -> BenchmarkStorage:
        pass


class ModelStorage(Protocol):
    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]:
        pass

    @staticmethod
    def get_or_create(
        model_name: str, model_hash: int, binary: bytes
    ) -> Result[ModelMetadataDomain, UnknownLunaBenchError]:
        pass

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, DataNotExistError | UnknownLunaBenchError]:
        pass


class BenchmarkStorage(Protocol):
    @staticmethod
    def create(benchmark_name: str) -> Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def load(benchmark_name: str) -> Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def delete(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def load_all() -> Result[list[BenchmarkDomain], UnknownLunaBenchError]:
        pass

    @staticmethod
    def set_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def remove_modelset(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def add_plot(benchmark_name: str, plot_name: str, plot_config: BaseModel) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        pass


class ModelSetStorage(Protocol):
    @staticmethod
    def create(modelset_name: str) -> Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def load(modelset_name: str) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def delete(modelset_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def add_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def remove_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        pass

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], UnknownLunaBenchError]:
        pass

    @staticmethod
    def load_all_models(
        modelset_name: str,
    ) -> Result[list[ModelMetadataDomain], DataNotExistError | UnknownLunaBenchError]:
        pass
