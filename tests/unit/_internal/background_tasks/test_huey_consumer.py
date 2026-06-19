import json
from unittest.mock import MagicMock, patch

from luna_bench._internal.background_tasks.huey.huey_background_task_client import HueyBackgroundTaskClient
from luna_bench.configs.config import config


class TestHueyConsumer:
    def test_config_override_propagates_worker_count(self) -> None:
        override = config.LB_ASYNC_WORKER_COUNT + 1
        config.LB_ASYNC_WORKER_COUNT = override

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            HueyBackgroundTaskClient._start_consumer()

            # The serialized config should be in the last argument.
            args = mock_popen.call_args[0][0]
            config_data = json.loads(args[-1])
            assert config_data["LB_ASYNC_WORKER_COUNT"] == override, (
                f"Expected {override}, got {config_data['LB_ASYNC_WORKER_COUNT']}"
            )

        # Clean up
        HueyBackgroundTaskClient._stop_consumer()
        config.LB_ASYNC_WORKER_COUNT = override - 1

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
