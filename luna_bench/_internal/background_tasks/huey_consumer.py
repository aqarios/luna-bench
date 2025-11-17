from __future__ import annotations

from contextlib import contextmanager
from multiprocessing import Process
from typing import TYPE_CHECKING

from huey import MemoryHuey, SqliteHuey
from huey.consumer import WORKER_THREAD, Consumer
from luna_quantum import Logging

from luna_bench.configs.config import config

if TYPE_CHECKING:
    from collections.abc import Generator


class HueyConsumer:
    _process: Process | None = None
    _logger = Logging.get_logger(__name__)

    huey: SqliteHuey | MemoryHuey = (
        MemoryHuey()
        if config.DB_JOBS_CONNECTION_STRING == ":memory:"
        else SqliteHuey("luna-bench-background_tasks", filename=config.DB_JOBS_CONNECTION_STRING)
    )

    @staticmethod
    def _run_consumer() -> None:  # pragma: no cover # another process, hart/impossible to measure coverage
        consumer = Consumer(
            HueyConsumer.huey,
            workers=config.ASYNC_WORKER_COUNT,
            periodic=True,
            initial_delay=0.1,
            backoff=1.15,
            max_delay=10.0,
            scheduler_interval=1,
            worker_type=WORKER_THREAD,
            check_worker_health=True,
            health_check_interval=1,
            flush_locks=True,
            extra_locks=None,
        )

        try:
            HueyConsumer._logger.debug("Huey consumer started.")
            consumer.run()  # does not install signal handlers

        finally:
            HueyConsumer._logger.debug("Huey consumer exiting.")
            consumer.stop()
            HueyConsumer._logger.debug("Huey consumer was stopped.")

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
        if HueyConsumer.is_consumer_running():
            cls._logger.debug("Huey consumer is already running. Stopping it first.")
            HueyConsumer._stop_consumer()

        cls._logger.debug("Starting background_tasks consumer in a new process.")
        cls._process = Process(target=HueyConsumer._run_consumer, name="background_tasks-consumer")
        cls._process.start()

    @classmethod
    def is_consumer_running(cls) -> bool:
        return cls._process is not None and cls._process.is_alive()

    @classmethod
    def start_if_not_running(cls) -> None:
        if not cls.is_consumer_running():
            cls._start_consumer()

    @classmethod
    @contextmanager
    def consumer(cls) -> Generator[None]:
        cls._start_consumer()
        try:
            yield
        finally:
            cls._stop_consumer()
