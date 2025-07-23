from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from luna_bench._internal.entities.model_set.dao import ModelSetDAO


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
    def model_set(self) -> ModelSetDAO:
        pass
