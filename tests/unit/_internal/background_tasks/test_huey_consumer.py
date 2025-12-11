from luna_bench._internal.background_tasks.huey.huey_background_task_client import HueyBackgroundTaskClient


class TestHueyConsumer:
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
