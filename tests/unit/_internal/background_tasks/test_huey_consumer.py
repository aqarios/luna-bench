from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from luna_bench._internal.background_tasks.huey.huey_background_task_client import HueyBackgroundTaskClient
from luna_bench.configs.config import config

if TYPE_CHECKING:
    from collections.abc import Iterator


class TestHueyConsumer:
    @pytest.fixture(autouse=True)
    def _cleanup_consumer(self) -> Iterator[None]:
        """Ensure no stale consumer process is left running before each test."""
        HueyBackgroundTaskClient._stop_consumer()
        yield
        HueyBackgroundTaskClient._stop_consumer()

    def test_config_override_propagates_worker_count(self) -> None:
        """Test that config.LB_ASYNC_WORKER_COUNT is serialised into the subprocess command."""
        override = config.LB_ASYNC_WORKER_COUNT + 1
        original = config.LB_ASYNC_WORKER_COUNT
        config.LB_ASYNC_WORKER_COUNT = override

        mock_process = MagicMock()
        mock_process.poll.return_value = None  # pretend it's running

        try:
            with patch(
                "luna_bench._internal.background_tasks.huey.huey_background_task_client.subprocess.Popen",
                return_value=mock_process,
            ) as mock_popen:
                HueyBackgroundTaskClient._start_consumer()
                assert HueyBackgroundTaskClient.is_consumer_running()

                # Verify the serialised config JSON contains the override value.
                _args, _kwargs = mock_popen.call_args
                process_args = _args[0] if _args else []  # the command list
                # The last CLI argument is config_json (the 4th positional arg in sys.argv)
                config_json_arg = process_args[-1]
                assert f'"LB_ASYNC_WORKER_COUNT":{override}' in config_json_arg.replace(" ", ""), (
                    f"Expected LB_ASYNC_WORKER_COUNT={override} in serialised config"
                )
        finally:
            HueyBackgroundTaskClient._stop_consumer()
            config.LB_ASYNC_WORKER_COUNT = original

    def test_huey_consumer(self) -> None:
        assert not HueyBackgroundTaskClient.is_consumer_running()
        HueyBackgroundTaskClient._start_consumer()
        assert HueyBackgroundTaskClient.is_consumer_running()
        HueyBackgroundTaskClient._start_consumer()
        assert HueyBackgroundTaskClient.is_consumer_running()

        HueyBackgroundTaskClient._stop_consumer()
        assert not HueyBackgroundTaskClient.is_consumer_running()
        HueyBackgroundTaskClient._stop_consumer()
        assert not HueyBackgroundTaskClient.is_consumer_running()

        with HueyBackgroundTaskClient.consumer():
            assert HueyBackgroundTaskClient.is_consumer_running()

        assert not HueyBackgroundTaskClient.is_consumer_running()
