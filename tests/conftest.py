pytest_plugins = [
    "tests.fixtures",
    "tests.e2e.fixtures",
    "tests.integration.fixtures",
    "tests.unit.fixtures",
]


def pytest_configure() -> None:
    from unittest.mock import MagicMock

    from luna_bench import _bg_task_container
    from luna_bench._internal.background_tasks import (
        BackgroundAlgorithmRunner,
        BackgroundTaskClient,
    )

    _bg_task_container.bg_task_client.override(MagicMock(spec=BackgroundTaskClient))
    _bg_task_container.bg_algorithm_runner.override(MagicMock(spec=BackgroundAlgorithmRunner))
