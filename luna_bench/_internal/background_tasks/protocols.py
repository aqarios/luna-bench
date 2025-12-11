from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Generator

    from luna_bench._internal.interfaces import AlgorithmAsync, AlgorithmSync


class BackgroundTaskClient(Protocol):
    @classmethod
    @contextmanager
    def consumer(cls) -> Generator[None]: ...


class BackgroundAlgorithmRunner(Protocol):
    @staticmethod
    def run_async[T: BaseModel](
        algorithm: AlgorithmAsync[T],
        model_id: int,
    ) -> str: ...

    @staticmethod
    def retrieve_task_result(
        task_id: str,
    ) -> Any | None: ...  # noqa: ANN401 # We don't know what the return type of "random" task is.

    @staticmethod
    def run_sync(
        algorithm: AlgorithmSync,
        model_id: int,
    ) -> str: ...
