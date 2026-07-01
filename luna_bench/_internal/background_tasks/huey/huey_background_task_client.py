from __future__ import annotations

import multiprocessing
import platform
import subprocess
import sys
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
    _process: subprocess.Popen[bytes] | None = None
    _huey: SqliteHuey | MemoryHuey | None = None
    _logger = Logging.get_logger(__name__)

    @staticmethod
    def huey() -> SqliteHuey | MemoryHuey:
        """Return the Huey instance, creating it lazily from the current config."""
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
            f"Initializing {config.resolved_jobs_db_connection_string} huey consumer with worker type: {worker_type}."
        )

        # The consumer runs in a fresh subprocess with an empty
        # TaskRegistry.  Register the algorithm task functions here so
        # it can resolve the task names it reads from the queue.
        from luna_bench._internal.background_tasks.huey.huey_algorithm_runner import (  # noqa: PLC0415
            HueyAlgorithmRunner,
        )

        huey = HueyBackgroundTaskClient.huey()
        HueyAlgorithmRunner.register_tasks(huey)

        consumer = Consumer(
            HueyBackgroundTaskClient.huey(),
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
            consumer.run()

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

        if cls._process.poll() is None:
            cls._logger.debug(
                f"Huey consumer is running and should be terminated. Will wait for {config.LB_HUEY_JOIN_TIMEOUT}sec "
                f"before force-killing."
            )
            cls._process.terminate()
            try:
                cls._process.wait(timeout=config.LB_HUEY_JOIN_TIMEOUT)
            except subprocess.TimeoutExpired:
                cls._logger.warning("Huey consumer did not terminate in time. Force-killing process.")
                cls._process.kill()
                cls._process.wait(timeout=config.LB_HUEY_JOIN_TIMEOUT)
            cls._logger.debug("Huey consumer stopped.")

        cls._process = None

    @classmethod
    def _start_consumer(cls) -> None:
        cls._logger.debug("Starting background_tasks consumer.")
        if HueyBackgroundTaskClient.is_consumer_running():
            cls._logger.debug("Huey consumer is already running. Stopping it first.")
            HueyBackgroundTaskClient._stop_consumer()

        cls._logger.debug("Starting background_tasks consumer in a new process.")

        # Serialize the parent's config so the child process sees the same values.
        config_json = config.model_dump_json()

        # Set config from JSON FIRST, then import the module. That way the
        # lazy huey() call in _run_consumer picks up the right values.
        bootstrap_code = (
            "import importlib,sys,json\n"
            "from luna_bench.configs.config import config as cfg\n"
            "for k, v in json.loads(sys.argv[3]).items():\n"
            "    setattr(cfg, k, v)\n"
            "obj=importlib.import_module(sys.argv[1])\n"
            "for part in sys.argv[2].split('.'):\n"
            "    obj=getattr(obj, part)\n"
            "obj._run_consumer()\n"
        )
        cls._process = subprocess.Popen(  # noqa: S603 # command is built from trusted class metadata
            [
                sys.executable,
                "-c",
                bootstrap_code,
                cls.__module__,
                cls.__qualname__,
                config_json,
            ]
        )

    @classmethod
    def is_consumer_running(cls) -> bool:
        return cls._process is not None and cls._process.poll() is None

    @classmethod
    @contextmanager
    def consumer(cls) -> Generator[None]:
        cls._start_consumer()
        try:
            yield
        finally:
            cls._stop_consumer()
