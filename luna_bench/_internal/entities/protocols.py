from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from types import TracebackType

    from returns.result import Result

    from luna_bench._internal.entities.model_set import ModelMetadataDomain, ModelSetDomain
    from luna_bench.errors.storage.data_not_exist_error import DataNotExistError


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
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError]:
        pass

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]:
        pass

    @staticmethod
    def get_or_create(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, Exception]:
        pass

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, DataNotExistError]:
        pass


class ModelSetStorage(Protocol):
    @staticmethod
    def create(name: str) -> Result[ModelSetDomain, DataNotUniqueError | Exception]:
        pass

    @staticmethod
    def load(modelset_id: int) -> Result[ModelSetDomain, Exception]:
        pass

    @staticmethod
    def delete(modelset_id: int) -> Result[None, Exception]:
        pass

    @staticmethod
    def add_model(modelset_id: int, model_id: int) -> Result[ModelSetDomain, Exception]:
        pass

    @staticmethod
    def remove_model(modelset_id: int, model_id: int) -> Result[ModelSetDomain, Exception]:
        pass

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], Exception]:
        pass

    @staticmethod
    def load_all_models(modelset_id: int) -> Result[list[ModelMetadataDomain], Exception]:
        pass
