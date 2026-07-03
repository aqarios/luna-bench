"""Core logging class for luna-bench."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from luna_bench.configs.config import config

from .log_level import LogLevel

if TYPE_CHECKING:
    from logging import Logger


class BenchLogger:
    """Configure and use loggers for luna-bench.

    Static methods to:
    - Get or set the global logging level
    - Create loggers with Rich formatting
    - Write logs to a file
    """

    _current_level: ClassVar[LogLevel] = config.LB_LOG_DEFAULT_LEVEL
    _file_handler: ClassVar[logging.FileHandler | None] = None

    @staticmethod
    def _luna_bench_loggers() -> list[Logger]:
        """Return all existing loggers whose name starts with ``"luna_bench"``."""
        return [
            logging.getLogger(name)
            for name in logging.root.manager.loggerDict  # type: ignore[attr-defined]
            if name.startswith("luna_bench")
        ]

    @staticmethod
    def _add_handler_if_missing(logger: Logger, handler: logging.FileHandler) -> None:
        """Add a FileHandler to a logger, skipping if one for the same path exists."""
        if not any(
            isinstance(h, logging.FileHandler) and h.baseFilename == handler.baseFilename  # type: ignore[attr-defined]
            for h in logger.handlers
        ):
            logger.addHandler(handler)

    @staticmethod
    def is_process_bar_shown() -> bool:
        """Return whether to show a progress bar / spinner.

        ``True`` when spinners are enabled by config and the log level
        is not NOTSET.
        """
        return not config.LB_LOG_DISABLE_SPINNER and BenchLogger.get_level() != logging.NOTSET

    @staticmethod
    def set_level(log_level: int | str | LogLevel) -> None:
        """Set the logging level for all luna-bench loggers and the file handler.

        Parameters
        ----------
        log_level : int | str | LogLevel
            Logging level to set.  Accepts ``LogLevel`` members, ``logging``
            module constants, numeric values, or strings like ``"DEBUG"``.
        """
        log_level = LogLevel.coerce(log_level)
        BenchLogger._current_level = log_level
        config.LB_LOG_DEFAULT_LEVEL = log_level

        for lgr in BenchLogger._luna_bench_loggers():
            lgr.setLevel(log_level)

        # Also update the shared file handler so it respects the new level.
        if BenchLogger._file_handler is not None:
            BenchLogger._file_handler.setLevel(log_level)

    @staticmethod
    def get_level() -> LogLevel:
        """Return the current logging level for luna-bench.

        Returns
        -------
        LogLevel
            Current logging level (e.g. ``LogLevel.INFO``, ``LogLevel.DEBUG``).
            Since ``LogLevel`` is an ``IntEnum``, it can be compared with
            integers (``get_level() >= logging.INFO``) and passed to the
            ``logging`` API.
        """
        return BenchLogger._current_level

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
        """Get a logger and add a RichHandler.

        Parameters
        ----------
        name : str
            Name of the logger to retrieve or create.

        Returns
        -------
        Logger
            Logger with a RichHandler and, if :meth:`setup_file_logging`
            was called, the shared file handler.
        """
        logger = logging.getLogger(name)
        logger.setLevel(BenchLogger.get_level())
        logger.propagate = False

        if not logger.hasHandlers():
            handler = RichHandler(
                console=BenchLogger.get_console(),
                rich_tracebacks=True,
                show_time=True,
                show_level=True,
                show_path=False,
                log_time_format="%Y-%m-%d %H:%M:%S",
            )
            logger.addHandler(handler)

        # Attach the shared file handler if configured (idempotent)
        if BenchLogger._file_handler is not None:
            BenchLogger._add_handler_if_missing(logger, BenchLogger._file_handler)

        return logger

    @staticmethod
    def setup_file_logging(log_dir: str, level: int | str | LogLevel | None = None) -> None:
        """Add a shared FileHandler to all luna-bench loggers.

        New loggers created via :meth:`get_logger` get this handler automatically.
        The log file name is taken from ``config.LB_LOG_FILE`` (default ``"main.txt"``).

        Parameters
        ----------
        log_dir : str
            Directory to write log files into (e.g. ``benchmark.data_dir_logs``).
        level : int | str | LogLevel | None
            Logging level for the file handler.  ``None`` (default) uses the
            current global log level from :meth:`get_level`.
        """
        level = BenchLogger.get_level() if level is None else LogLevel.coerce(level)

        log_path = Path(log_dir) / config.LB_LOG_FILE
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(str(log_path))
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        BenchLogger._file_handler = handler

        for lgr in BenchLogger._luna_bench_loggers():
            BenchLogger._add_handler_if_missing(lgr, handler)
