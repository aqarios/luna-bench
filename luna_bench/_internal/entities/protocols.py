from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType

    from returns.result import Result

    from luna_bench._internal.entities.model_set import ModelMetadataDomain, ModelSetDomain


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
    def get(model_hash: int) -> Result[ModelMetadataDomain, str]:
        pass

    @staticmethod
    def get_all() -> Result[list[ModelMetadataDomain], str]:
        pass

    @staticmethod
    def get_or_create(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, str]:
        pass

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, str]:
        pass


class ModelSetStorage(Protocol):
    @staticmethod
    def create(name: str) -> Result[ModelSetDomain, str]:
        pass

    @staticmethod
    def load(modelset_id: int) -> Result[ModelSetDomain, str]:
        pass

    @staticmethod
    def delete(modelset_id: int) -> Result[None, str]:
        pass

    @staticmethod
    def add_model(modelset_id: int, model_id: int) -> Result[ModelSetDomain, str]:
        pass

    @staticmethod
    def remove_model(modelset_id: int, model_id: int) -> Result[ModelSetDomain, str]:
        pass

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], str]:
        pass

    @staticmethod
    def load_all_models(modelset_id: int) -> Result[list[ModelMetadataDomain], str]:
        pass
