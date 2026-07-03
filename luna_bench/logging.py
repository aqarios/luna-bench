from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from luna_bench.configs.config import config

if TYPE_CHECKING:
    from logging import Logger


class Logging:
    """Utilities for configuring and accessing luna-bench loggers.

    This class provides static methods to:
    - Set and retrieve the global logging level for luna-bench components
    - Create and configure loggers with Rich formatting
    - Manage consistent logging behavior across the luna-bench codebase
    - Configure file logging to the benchmark output directory
    """

    _file_handler: ClassVar[logging.FileHandler | None] = None

    @staticmethod
    def is_process_bar_shown() -> bool:
        """Return whether to show a progress bar / spinner.

        Returns
        -------
        bool
            ``True`` if spinners should be shown (enabled by config and level
            is not NOTSET).
        """
        return not config.LB_LOG_DISABLE_SPINNER and Logging.get_level() != logging.NOTSET

    @staticmethod
    def set_level(log_level: int) -> None:
        """Set the logging level for all luna-bench loggers.

        Parameters
        ----------
        log_level : int
            Logging level to set (e.g., ``logging.DEBUG``, ``logging.INFO``).
        """
        config.LB_LOG_DEFAULT_LEVEL = logging.getLevelName(log_level)

        for logger_name in logging.root.manager.loggerDict:  # type: ignore[attr-defined]
            if logger_name.startswith("luna_bench"):
                logging.getLogger(logger_name).setLevel(log_level)

    @staticmethod
    def get_level() -> int:
        """Return the current logging level for luna-bench.

        Returns
        -------
        int
            Current logging level as defined in the ``logging`` module
            (e.g., ``logging.DEBUG``, ``logging.INFO``, etc.).
        """
        return logging._nameToLevel.get(  # type: ignore[attr-defined]
            config.LB_LOG_DEFAULT_LEVEL, logging.INFO
        )

    @staticmethod
    def get_console() -> Console:
        """Return a Rich console instance for use in logging.

        Returns
        -------
        Console
            A Rich Console with a themed colour scheme for log levels.
        """
        custom_theme = Theme(
            {
                "logging.level.debug": "bright_blue",
                "logging.level.info": "bright_green",
                "logging.level.warning": "bold bright_yellow",
                "logging.level.error": "bold bright_red",
                "logging.level.critical": "bold bright_magenta",
            }
        )
        return Console(theme=custom_theme)

    @staticmethod
    def get_logger(name: str) -> Logger:
        """Get a logger with the specified name and set up a RichHandler for it.

        Parameters
        ----------
        name : str
            Name of the logger to retrieve or create.

        Returns
        -------
        Logger
            Configured logger instance with a RichHandler (and an optional shared
            file handler if :meth:`setup_file_logging` was called).
        """
        logger = logging.getLogger(name)
        logger.setLevel(Logging.get_level())
        logger.propagate = False

        if not logger.hasHandlers():
            handler = RichHandler(
                console=Logging.get_console(),
                rich_tracebacks=True,
                show_time=True,
                show_level=True,
                show_path=False,
                log_time_format="%Y-%m-%d %H:%M:%S",
            )
            logger.addHandler(handler)

        # Attach the shared file handler if configured (idempotent)
        file_handler = Logging._file_handler
        if file_handler is not None and not any(
            isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename  # type: ignore[attr-defined]
            for h in logger.handlers
        ):
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def setup_file_logging(log_dir: str, level: int = logging.INFO) -> None:
        """Configure file logging for all luna-bench loggers.

        Adds a ``FileHandler`` to every existing luna-bench logger and to all
        loggers created afterwards via :meth:`get_logger`.

        Parameters
        ----------
        log_dir : str
            Directory to write log files into (e.g. ``benchmark.data_dir_logs``).
        level : int
            Logging level for the file handler (default ``logging.INFO``).
        """
        log_path = Path(log_dir) / "luna-bench.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(str(log_path))
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        Logging._file_handler = handler

        # Attach to every existing luna-bench logger (idempotent)
        for logger_name in logging.root.manager.loggerDict:  # type: ignore[attr-defined]
            if logger_name.startswith("luna_bench"):
                logger = logging.getLogger(logger_name)
                if not any(
                    isinstance(h, logging.FileHandler) and h.baseFilename == handler.baseFilename  # type: ignore[attr-defined]
                    for h in logger.handlers
                ):
                    logger.addHandler(handler)
