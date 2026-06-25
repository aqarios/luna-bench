from __future__ import annotations

import platform
import threading
from contextlib import contextmanager
from pathlib import Path
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
    _thread: threading.Thread | None = None
    _consumer: Consumer | None = None
    _consumer_ready: threading.Event = threading.Event()

    _logger = Logging.get_logger(__name__)
    _huey: SqliteHuey | MemoryHuey | None = None

    @staticmethod
    def huey() -> SqliteHuey | MemoryHuey:
        if HueyBackgroundTaskClient._huey is None:
            filename = config.resolved_jobs_db_connection_string
            HueyBackgroundTaskClient._logger.debug(f"Initializing huey with filename: {filename}.")
            if filename != ":memory:":
                Path(filename).parent.mkdir(parents=True, exist_ok=True)
            HueyBackgroundTaskClient._huey = (
                MemoryHuey()
                if filename == ":memory:"
                else SqliteHuey(
                    name="luna-bench-background_tasks",
                    filename=filename,
                    timeout=30,
                    journal_mode="wal",
                )
            )
        return HueyBackgroundTaskClient._huey

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
                HueyBackgroundTaskClient._logger.debug("For your OS Darwin, the default worker type is 'process'.")
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
    def _run_consumer() -> None:  # pragma: no cover
        """Run the Huey consumer in a background thread."""
        worker_type = HueyBackgroundTaskClient._get_worker_type()
        HueyBackgroundTaskClient._logger.debug(
            f"Initializing {config.resolved_jobs_db_connection_string} huey consumer with worker type: {worker_type}."
        )
        huey = HueyBackgroundTaskClient.huey()
        consumer = Consumer(
            huey,
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

        # Disable signal handlers — signal.signal() only works in the main
        # thread, and this consumer runs in a background thread.
        consumer._set_signal_handlers = lambda: None  # noqa: SLF001

        # Publish the consumer reference so _stop_consumer can call .stop()
        HueyBackgroundTaskClient._consumer = consumer
        HueyBackgroundTaskClient._consumer_ready.set()

        try:
            HueyBackgroundTaskClient._logger.debug("Huey consumer started.")
            consumer.run()

        finally:
            HueyBackgroundTaskClient._logger.debug("Huey consumer exiting.")
            consumer.stop()
            HueyBackgroundTaskClient._consumer = None
            HueyBackgroundTaskClient._consumer_ready.clear()
            HueyBackgroundTaskClient._logger.debug("Huey consumer was stopped.")

    @classmethod
    def _stop_consumer(cls) -> None:
        cls._logger.debug("Stopping background_tasks consumer.")

        if cls._thread is None:
            cls._logger.debug("Huey consumer is not running.")
            return

        if cls._thread.is_alive():
            cls._logger.debug(
                f"Huey consumer is running and should be terminated. Will wait for {config.LB_HUEY_JOIN_TIMEOUT}sec "
                f"before force-killing."
            )

            # Wait for the consumer to be ready, then signal it to stop.
            cls._consumer_ready.wait()
            if cls._consumer is not None:
                cls._consumer.stop()

            cls._thread.join(timeout=config.LB_HUEY_JOIN_TIMEOUT)
            if cls._thread.is_alive():
                cls._logger.warning("Huey consumer did not terminate in time.")
            cls._logger.debug("Huey consumer stopped.")

        cls._thread = None
        cls._consumer = None

    @classmethod
    def _start_consumer(cls) -> None:
        cls._logger.debug("Starting background_tasks consumer.")
        if HueyBackgroundTaskClient.is_consumer_running():
            cls._logger.debug("Huey consumer is already running. Stopping it first.")
            HueyBackgroundTaskClient._stop_consumer()

        cls._logger.debug("Starting background_tasks consumer in a background thread.")

        cls._consumer_ready.clear()
        cls._thread = threading.Thread(
            target=HueyBackgroundTaskClient._run_consumer,
            daemon=True,
        )
        cls._thread.start()

    @classmethod
    def is_consumer_running(cls) -> bool:
        return cls._thread is not None and cls._thread.is_alive()

    @classmethod
    @contextmanager
    def consumer(cls) -> Generator[None]:
        cls._start_consumer()
        try:
            yield
        finally:
            cls._stop_consumer()
