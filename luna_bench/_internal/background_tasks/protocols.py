from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Generator

    from luna_bench.custom import BaseAlgorithmAsync, BaseAlgorithmSync


class BackgroundTaskClient(Protocol):
    """Protocol for managing the lifecycle of a background task consumer (worker subprocess)."""

    @classmethod
    @contextmanager
    def consumer(cls) -> Generator[None]:
        """
        Context manager that starts and stops a background task consumer subprocess.

        On ``__enter__`` a subprocess running a queue consumer (e.g. a Huey
        ``Consumer`` event loop) is spawned.  On ``__exit__`` the subprocess
        is terminated.  While the consumer is active, tasks enqueued by
        ``BackgroundAlgorithmRunner`` are picked up and executed.

        Yields
        ------
        None
        """


class BackgroundAlgorithmRunner(Protocol):
    """Protocol for submitting algorithms to a background task queue for execution."""

    @staticmethod
    def run_async[T: BaseModel](
        algorithm: BaseAlgorithmAsync[T],
        model_id: int,
    ) -> str:
        """
        Enqueue an async algorithm for execution and return immediately.

        Parameters
        ----------
        algorithm: BaseAlgorithmAsync[T]
            The algorithm to execute asynchronously.
        model_id: int
            The id of the model to run the algorithm on.

        Returns
        -------
        str
            The task id string for tracking the background task.
        """

    @staticmethod
    def retrieve_task_result(
        task_id: str,
    ) -> Any | None:  # noqa: ANN401 # We don't know what the return type of "random" task is.
        """
        Non-blocking lookup of a previously submitted task's result.

        Parameters
        ----------
        task_id: str
            The task id to retrieve the result for.

        Returns
        -------
        Any | None
            The result of the task if available, or None if not yet completed.
        """

    @staticmethod
    def run_sync(
        algorithm: BaseAlgorithmSync,
        model_id: int,
    ) -> str:
        """
        Enqueue a synchronous algorithm for deferred execution and return immediately.

        Despite the method name, the algorithm is **not** executed synchronously. The solution is calculated
        inside the algorithm synchronously. When the task is done, a solution object is the result of this task.

        Parameters
        ----------
        algorithm: BaseAlgorithmSync
            The algorithm to execute synchronously.
        model_id: int
            The id of the model to run the algorithm on.

        Returns
        -------
        str
            The task id string for tracking the background task.
        """
