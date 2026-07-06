from __future__ import annotations

import logging
from typing import cast

import pytest
from pydantic import ValidationError

from luna_bench.configs.config import Config
from luna_bench.logging import LogLevel


class TestLogLevel:
    """LogLevel.coerce() — all branches."""

    def test_coerce_passthrough(self) -> None:
        """LogLevel member passes through unchanged."""
        assert LogLevel.coerce(LogLevel.DEBUG) is LogLevel.DEBUG

    def test_coerce_from_str(self) -> None:
        """String name to LogLevel."""
        assert LogLevel.coerce("WARNING") is LogLevel.WARNING

    def test_coerce_from_str_case_insensitive(self) -> None:
        """Lowercase string to LogLevel."""
        assert LogLevel.coerce("debug") is LogLevel.DEBUG

    def test_coerce_from_int(self) -> None:
        """Logging constant to LogLevel."""
        assert LogLevel.coerce(logging.INFO) is LogLevel.INFO

    def test_coerce_from_int_value(self) -> None:
        """Raw int to LogLevel."""
        assert LogLevel.coerce(50) is LogLevel.CRITICAL

    def test_coerce_invalid_str_raises(self) -> None:
        """Invalid string raises KeyError."""
        with pytest.raises(KeyError, match="INVALID"):
            LogLevel.coerce("INVALID")


class TestConfigLogLevel:
    """Pydantic validation of LB_LOG_DEFAULT_LEVEL."""

    def test_default_is_info(self) -> None:
        """Default config has INFO level."""
        c = Config()
        assert c.LB_LOG_DEFAULT_LEVEL == LogLevel.INFO

    def test_from_str_name(self) -> None:
        """String name parsed to LogLevel."""
        c = Config(LB_LOG_DEFAULT_LEVEL=cast("LogLevel", "DEBUG"))
        assert c.LB_LOG_DEFAULT_LEVEL == LogLevel.DEBUG

    def test_from_int_value(self) -> None:
        """Raw int parsed to LogLevel."""
        c = Config(LB_LOG_DEFAULT_LEVEL=cast("LogLevel", 50))
        assert c.LB_LOG_DEFAULT_LEVEL == LogLevel.CRITICAL

    def test_from_log_level_member(self) -> None:
        """LogLevel member passes through."""
        c = Config(LB_LOG_DEFAULT_LEVEL=LogLevel.WARNING)
        assert c.LB_LOG_DEFAULT_LEVEL == LogLevel.WARNING

    def test_invalid_raises(self) -> None:
        """Invalid string raises ValidationError."""
        with pytest.raises((ValidationError, ValueError)):
            Config(LB_LOG_DEFAULT_LEVEL=cast("LogLevel", "INVALID"))


class TestConfigDbPaths:
    """resolved_db_connection_string and resolved_jobs_db_connection_string."""

    def test_resolved_db_default_path(self) -> None:
        """Default DB path when no connection string is set."""
        c = Config(LB_DB_CONNECTION_STRING="", LB_DATA_DIR="/tmp/test_luna")
        assert "database/luna_bench.db" in c.resolved_db_connection_string

    def test_resolved_jobs_db_default_path(self) -> None:
        """Default jobs DB path when no connection string is set."""
        c = Config(LB_DB_JOBS_CONNECTION_STRING="", LB_DATA_DIR="/tmp/test_luna")
        assert "database/luna_bench-jobs.db" in c.resolved_jobs_db_connection_string

    def test_resolved_db_custom_string(self) -> None:
        """Custom connection string returned directly."""
        c = Config(LB_DB_CONNECTION_STRING="/custom/path.db")
        assert c.resolved_db_connection_string == "/custom/path.db"

    def test_resolved_jobs_db_custom_string(self) -> None:
        """Custom jobs connection string returned directly."""
        c = Config(LB_DB_JOBS_CONNECTION_STRING="/custom/jobs.db")
        assert c.resolved_jobs_db_connection_string == "/custom/jobs.db"
