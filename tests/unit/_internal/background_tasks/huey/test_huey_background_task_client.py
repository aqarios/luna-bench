from __future__ import annotations

from unittest.mock import patch

import pytest
from huey.consumer import WORKER_GREENLET, WORKER_PROCESS, WORKER_THREAD

from luna_bench._internal.background_tasks.huey.huey_background_task_client import HueyBackgroundTaskClient
from luna_bench.errors.invalid_worker_type_error import InvalidWorkerTypeError


class TestHueyBackgroundTaskClient:
    @pytest.mark.parametrize(
        ("env_value", "expected_worker_type"),
        [
            ("process", WORKER_PROCESS),
            ("thread", WORKER_THREAD),
            ("greenlet", WORKER_GREENLET),
            ("PROCESS", WORKER_PROCESS),
            ("THREAD", WORKER_THREAD),
            ("GREENLET", WORKER_GREENLET),
            ("ProCeSs", WORKER_PROCESS),
            ("ThReAd", WORKER_THREAD),
        ],
        ids=[
            "lowercase_process",
            "lowercase_thread",
            "lowercase_greenlet",
            "uppercase_process",
            "uppercase_thread",
            "uppercase_greenlet",
            "mixed_case_process",
            "mixed_case_thread",
        ],
    )
    def test_get_worker_type_from_env_valid(self, env_value: str, expected_worker_type: str) -> None:
        """Test that valid environment variables are accepted and lowercased correctly."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", env_value):
            result = HueyBackgroundTaskClient._get_worker_type()
            assert result == expected_worker_type

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "invalid",
            "worker",
            "pool",
            "async",
            "multiprocess",
            "",
            "123",
            "process_pool",
        ],
        ids=[
            "invalid_string",
            "worker_string",
            "pool_string",
            "async_string",
            "multiprocess_string",
            "empty_string",
            "number_string",
            "compound_string",
        ],
    )
    def test_get_worker_type_from_env_invalid(self, invalid_value: str) -> None:
        """Test that invalid environment variables raise InvalidWorkerTypeError."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", invalid_value):
            with pytest.raises(InvalidWorkerTypeError) as exc_info:
                HueyBackgroundTaskClient._get_worker_type()

            assert exc_info.value.worker_type == invalid_value
            assert WORKER_PROCESS in exc_info.value.valid_types
            assert WORKER_THREAD in exc_info.value.valid_types
            assert WORKER_GREENLET in exc_info.value.valid_types

    @pytest.mark.parametrize(
        ("platform_name", "expected_worker_type"),
        [
            ("Windows", WORKER_THREAD),
            ("Darwin", WORKER_PROCESS),
            ("Linux", WORKER_PROCESS),
            ("FreeBSD", WORKER_THREAD),  # Unknown OS defaults to thread
            ("Unknown", WORKER_THREAD),
            ("SunOS", WORKER_THREAD),
        ],
        ids=[
            "windows_system",
            "darwin_system",
            "linux_system",
            "freebsd_system",
            "unknown_system",
            "sunos_system",
        ],
    )
    def test_get_worker_type_from_platform_no_env(self, platform_name: str, expected_worker_type: str) -> None:
        """Test that correct worker type is selected based on OS when env var is not set."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", None), patch("platform.system", return_value=platform_name):
            result = HueyBackgroundTaskClient._get_worker_type()
            assert result == expected_worker_type

    def test_get_worker_type_env_overrides_platform(self) -> None:
        """Test that the environment variable takes precedence over platform detection."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", "process"), patch("platform.system", return_value="Windows"):
            result = HueyBackgroundTaskClient._get_worker_type()

            assert result == WORKER_PROCESS

    def test_get_worker_type_env_none_uses_platform(self) -> None:
        """Test that None environment variable triggers platform detection."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", None), patch("platform.system", return_value="Linux"):
            result = HueyBackgroundTaskClient._get_worker_type()
            assert result == WORKER_PROCESS

    def test_get_worker_type_darwin_sets_fork_method(self) -> None:
        """Test that Darwin OS sets a multiprocessing start method to 'fork'."""
        from luna_bench.configs.config import config

        with (
            patch.object(config, "LB_HUEY_WORKER_TYPE", None),
            patch("platform.system", return_value="Darwin"),
            patch("multiprocessing.set_start_method") as mock_set_method,
        ):
            result = HueyBackgroundTaskClient._get_worker_type()
            assert result == WORKER_PROCESS
            mock_set_method.assert_called_once_with("fork", force=True)

    @pytest.mark.parametrize(
        ("env_value", "exception_type"),
        [
            ("not_a_worker_type", InvalidWorkerTypeError),
            ("INVALID", InvalidWorkerTypeError),
            ("pool", InvalidWorkerTypeError),
        ],
    )
    def test_get_worker_type_invalid_env_raises_specific_error(
        self, env_value: str, exception_type: type[InvalidWorkerTypeError]
    ) -> None:
        """Test that a specific error type is raised for invalid env values."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", env_value), pytest.raises(exception_type):
            HueyBackgroundTaskClient._get_worker_type()

    @pytest.mark.parametrize(
        "os_name",
        ["Windows", "Darwin", "Linux"],
        ids=["windows_default", "darwin_default", "linux_default"],
    )
    def test_get_worker_type_all_known_os_returns_valid_type(self, os_name: str) -> None:
        """Test that all known OS names return valid worker types."""
        from luna_bench.configs.config import config

        with patch.object(config, "LB_HUEY_WORKER_TYPE", None), patch("platform.system", return_value=os_name):
            result = HueyBackgroundTaskClient._get_worker_type()

            valid_types = {WORKER_PROCESS, WORKER_THREAD, WORKER_GREENLET}
            assert result in valid_types
