from luna_bench._internal.background_tasks.huey_consumer import HueyConsumer


class TestHueyConsumer:
    def test_huey_consumer(self) -> None:
        assert not HueyConsumer.is_consumer_running()
        HueyConsumer.start_if_not_running()
        assert HueyConsumer.is_consumer_running()
        HueyConsumer._start_consumer()
        assert HueyConsumer.is_consumer_running()

        HueyConsumer._stop_consumer()
        assert not HueyConsumer.is_consumer_running()
        HueyConsumer._stop_consumer()
        assert not HueyConsumer.is_consumer_running()

        with HueyConsumer.consumer():
            assert HueyConsumer.is_consumer_running()

        assert not HueyConsumer.is_consumer_running()
