from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType

    from returns.result import Result

    from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain
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


class BenchmarkDao(Protocol):
    @staticmethod
    def create(modelset_name: str) -> Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]:
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
