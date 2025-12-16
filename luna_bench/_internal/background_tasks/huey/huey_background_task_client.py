from __future__ import annotations

from contextlib import contextmanager
from multiprocessing import Process
from typing import TYPE_CHECKING

from huey import MemoryHuey, SqliteHuey
from huey.consumer import WORKER_PROCESS, Consumer
from luna_quantum import Logging

from luna_bench._internal.background_tasks.protocols import BackgroundTaskClient
from luna_bench.configs.config import config

if TYPE_CHECKING:
    from collections.abc import Generator


class HueyBackgroundTaskClient(BackgroundTaskClient):
    _process: Process | None = None
    _logger = Logging.get_logger(__name__)

    huey: SqliteHuey | MemoryHuey = (
        MemoryHuey()
        if config.DB_JOBS_CONNECTION_STRING == ":memory:"
        else SqliteHuey(
            name="luna-bench-background_tasks",
            filename=config.DB_JOBS_CONNECTION_STRING,
            timeout=30,
            journal_mode="wal",
        )
    )

    @staticmethod
    def _run_consumer() -> None:  # pragma: no cover # another process, hart/impossible to measure coverage
        consumer = Consumer(
            HueyBackgroundTaskClient.huey,
            workers=config.ASYNC_WORKER_COUNT,
            periodic=True,
            initial_delay=0.1,
            backoff=1.15,
            max_delay=10.0,
            scheduler_interval=1,
            worker_type=WORKER_PROCESS,
            check_worker_health=True,
            health_check_interval=1,
            flush_locks=True,
            extra_locks=None,
        )

        try:
            HueyBackgroundTaskClient._logger.debug("Huey consumer started.")
            consumer.run()  # does not install signal handlers

        finally:
            HueyBackgroundTaskClient._logger.debug("Huey consumer exiting.")
            consumer.stop()
            HueyBackgroundTaskClient._logger.debug("Huey consumer was stopped.")

    @classmethod
    def _stop_consumer(cls) -> None:
        cls._logger.debug("Stopping background_tasks consumer.")

        if cls._process is None:
            cls._logger.debug("Huey consumer is not running.")

            return

        if cls._process.is_alive():
            cls._logger.debug("Huey consumer is running and should be terminated.")
            cls._process.terminate()
            cls._process.join(timeout=30)
            cls._logger.debug("Huey consumer stopped.")
            cls._process = None

    @classmethod
    def _start_consumer(cls) -> None:
        cls._logger.debug("Starting background_tasks consumer.")
        if HueyBackgroundTaskClient.is_consumer_running():
            cls._logger.debug("Huey consumer is already running. Stopping it first.")
            HueyBackgroundTaskClient._stop_consumer()

        cls._logger.debug("Starting background_tasks consumer in a new process.")
        cls._process = Process(target=HueyBackgroundTaskClient._run_consumer, name="background_tasks-consumer")
        cls._process.start()

    @classmethod
    def is_consumer_running(cls) -> bool:
        return cls._process is not None and cls._process.is_alive()

    @classmethod
    @contextmanager
    def consumer(cls) -> Generator[None]:
        cls._start_consumer()
        try:
            yield
        finally:
            cls._stop_consumer()
