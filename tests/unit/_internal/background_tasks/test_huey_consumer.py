from __future__ import annotations

import threading
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from huey.consumer import Consumer

from luna_bench._internal.background_tasks.huey.huey_background_task_client import HueyBackgroundTaskClient
from luna_bench.configs.config import config

if TYPE_CHECKING:
    from collections.abc import Iterator


class TestHueyConsumer:
    @pytest.fixture(autouse=True)
    def _cleanup_consumer(self) -> Iterator[None]:
        """Ensure no stale consumer thread is left running before each test."""
        HueyBackgroundTaskClient._stop_consumer()
        yield
        HueyBackgroundTaskClient._stop_consumer()

    def test_config_override_propagates_worker_count(self) -> None:
        """Test that config.LB_ASYNC_WORKER_COUNT is passed to the Consumer."""
        override = config.LB_ASYNC_WORKER_COUNT + 1
        original = config.LB_ASYNC_WORKER_COUNT
        config.LB_ASYNC_WORKER_COUNT = override

        run_blocker = threading.Event()
        try:
            mock_consumer = MagicMock(spec=Consumer)
            mock_consumer.run.side_effect = lambda: run_blocker.wait()

            with patch(
                "luna_bench._internal.background_tasks.huey.huey_background_task_client.Consumer",
                return_value=mock_consumer,
            ) as mock_consumer_cls:
                HueyBackgroundTaskClient._start_consumer()
                HueyBackgroundTaskClient._consumer_ready.wait(timeout=5)

                assert HueyBackgroundTaskClient.is_consumer_running()
                mock_consumer_cls.assert_called_once()
                _args, kwargs = mock_consumer_cls.call_args
                assert kwargs.get("workers") == override, f"Expected workers={override}, got {kwargs}"
        finally:
            run_blocker.set()
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
