from __future__ import annotations

import platform
from contextlib import contextmanager
from multiprocessing import Process
from typing import TYPE_CHECKING, cast

from huey import MemoryHuey, SqliteHuey
from huey.consumer import WORKER_GREENLET, WORKER_PROCESS, WORKER_THREAD, Consumer
from luna_quantum import Logging

from luna_bench._internal.background_tasks.protocols import BackgroundTaskClient
from luna_bench.configs.config import config
from luna_bench.errors.invalid_worker_type_error import InvalidWorkerTypeError

if TYPE_CHECKING:
    from collections.abc import Generator


class HueyBackgroundTaskClient(BackgroundTaskClient):
    _process: Process | None = None
    _logger = Logging.get_logger(__name__)

    huey: SqliteHuey | MemoryHuey = (
        MemoryHuey()
        if config.LB_DB_JOBS_CONNECTION_STRING == ":memory:"
        else SqliteHuey(
            name="luna-bench-background_tasks",
            filename=config.LB_DB_JOBS_CONNECTION_STRING,
            timeout=30,
            journal_mode="wal",
        )
    )

    @staticmethod
    def _get_worker_type() -> str:
        """
        Determine the appropriate worker type for Huey based on OS or environment override.

        Returns
        -------
        str
            The worker type to use: 'process', 'thread', or 'greenlet'

        Raises
        ------
        InvalidWorkerTypeError
            If LB_HUEY_WORKER_TYPE is set to an invalid value
        """
        if config.LB_HUEY_WORKER_TYPE is not None:
            HueyBackgroundTaskClient._logger.debug(
                f"Using environment variable LB_HUEY_WORKER_TYPE with value {config.LB_HUEY_WORKER_TYPE} "
                f"for the worker type."
            )
            worker_type = config.LB_HUEY_WORKER_TYPE.lower()
            valid_types = {WORKER_PROCESS, WORKER_THREAD, WORKER_GREENLET}
            if worker_type not in valid_types:
                raise InvalidWorkerTypeError(worker_type, valid_types)
            return worker_type

        system = platform.system()
        HueyBackgroundTaskClient._logger.debug(f"Auto-detecting worker type for OS: '{system}'.")
        match system:
            case "Windows":
                return cast("str", WORKER_THREAD)
            case "Darwin":
                import multiprocessing  # noqa: PLC0415 # Import here since we only need it for Darwin machines

                multiprocessing.set_start_method("fork", force=True)
                HueyBackgroundTaskClient._logger.debug(
                    "For your OS Darwin, the default worker type is 'process'. But we have to set the start method"
                    "to 'fork' (since huey relies on that). This is no longer the default on Darwin. If you face issues"
                    "With that, consider setting LB_HUEY_WORKER_TYPE=thread."
                )
                return cast("str", WORKER_PROCESS)
            case "Linux":
                return cast("str", WORKER_PROCESS)
            case _:
                HueyBackgroundTaskClient._logger.warning(
                    f"For your OS '{system}', there is no specific worker type set. "
                    f"You can force a specific worker type by setting the LB_HUEY_WORKER_TYPE environment variable."
                    f"The default worker type is 'thread' since it causes overall less issues on various OSes."
                )
                return cast("str", WORKER_THREAD)

    @staticmethod
    def _run_consumer() -> None:  # pragma: no cover # another process, hart/impossible to measure coverage
        worker_type = HueyBackgroundTaskClient._get_worker_type()
        HueyBackgroundTaskClient._logger.debug(
            f"Initializing {config.LB_DB_JOBS_CONNECTION_STRING} huey consumer with worker type: {worker_type}."
        )
        consumer = Consumer(
            HueyBackgroundTaskClient.huey,
            workers=config.LB_ASYNC_WORKER_COUNT,
            periodic=True,
            initial_delay=0.1,
            backoff=1.15,
            max_delay=10.0,
            scheduler_interval=1,
            worker_type=worker_type,
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
            cls._logger.debug(
                f"Huey consumer is running and should be terminated. Will wait for {config.LB_HUEY_JOIN_TIMEOUT}sec "
                f"before force-killing."
            )
            cls._process.terminate()
            cls._process.join(timeout=config.LB_HUEY_JOIN_TIMEOUT)
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
