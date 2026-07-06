from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from pathlib import Path


class TestBenchLogger:
    """BenchLogger methods."""

    def test_get_level_default(self) -> None:
        """get_level returns INFO by default."""
        assert BenchLogger.get_level() == 20  # LogLevel.INFO

    def test_set_level_int(self) -> None:
        """set_level with a logging constant."""
        BenchLogger.set_level(logging.DEBUG)
        assert BenchLogger.get_level() == logging.DEBUG
        BenchLogger.set_level(logging.INFO)  # reset

    def test_set_level_str(self) -> None:
        """set_level with a string."""
        BenchLogger.set_level("WARNING")
        assert BenchLogger.get_level() == 30  # LogLevel.WARNING
        BenchLogger.set_level("INFO")  # reset

    def test_set_level_log_level(self) -> None:
        """set_level with a LogLevel member."""
        from luna_bench.logging import LogLevel

        BenchLogger.set_level(LogLevel.ERROR)
        assert BenchLogger.get_level() == 40  # LogLevel.ERROR
        BenchLogger.set_level(LogLevel.INFO)  # reset

    def test_set_level_updates_loggers(self) -> None:
        """set_level updates existing luna_bench loggers."""
        logger = BenchLogger.get_logger("luna_bench.test_logger")
        BenchLogger.set_level(logging.DEBUG)
        assert logger.level == logging.DEBUG
        BenchLogger.set_level(logging.INFO)

    def test_set_level_updates_file_handler(self, tmp_path: Path) -> None:
        """set_level updates the file handler level."""
        log_dir = str(tmp_path)
        log_path = tmp_path / "main.txt"
        BenchLogger.setup_file_logging(log_dir)

        BenchLogger.set_level(logging.WARNING)
        assert BenchLogger._file_handler is not None
        assert BenchLogger._file_handler.level == logging.WARNING

        # cleanup
        BenchLogger._file_handler = None
        log_path.unlink(missing_ok=True)

    def test_setup_file_logging_creates_file(self, tmp_path: Path) -> None:
        """setup_file_logging creates the log file."""
        log_dir = str(tmp_path)
        log_path = tmp_path / "main.txt"
        BenchLogger.setup_file_logging(log_dir)

        assert log_path.exists()
        assert BenchLogger._file_handler is not None

        # cleanup
        BenchLogger._file_handler = None
        log_path.unlink(missing_ok=True)

    def test_setup_file_logging_target_logger(self, tmp_path: Path) -> None:
        """setup_file_logging with target_logger."""
        log_dir = str(tmp_path)
        log_path = tmp_path / "main.txt"

        BenchLogger.setup_file_logging(
            log_dir,
            target_logger="luna_bench.test_target_logger",
        )

        assert log_path.exists()
        # _file_handler should NOT be set in targeted mode
        assert BenchLogger._file_handler is None

        targeted = logging.getLogger("luna_bench.test_target_logger")
        assert any(
            isinstance(h, logging.FileHandler) and str(log_path) in str(h.baseFilename) for h in targeted.handlers
        )

        log_path.unlink(missing_ok=True)

    def test_is_process_bar_shown_disabled_in_test_env(self) -> None:
        """Spinner is disabled in test env."""
        from luna_bench.configs.config import config as _cfg

        assert _cfg.LB_LOG_DISABLE_SPINNER
        assert not BenchLogger.is_process_bar_shown()

    def test_get_logger_returns_logger(self) -> None:
        """get_logger returns a logger."""
        lgr = BenchLogger.get_logger("luna_bench.test_get_logger")
        assert lgr is not None
        assert lgr.name == "luna_bench.test_get_logger"

    def test_get_logger_level(self) -> None:
        """get_logger sets the level from get_level()."""
        BenchLogger.set_level(logging.INFO)
        lgr = BenchLogger.get_logger("luna_bench.test_get_logger_level")
        assert lgr.level == logging.INFO
        assert not lgr.propagate
