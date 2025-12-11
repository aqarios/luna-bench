from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from .huey.huey_algorithm_runner import HueyAlgorithmRunner
from .huey.huey_background_task_client import HueyBackgroundTaskClient

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from .protocols import BackgroundAlgorithmRunner, BackgroundTaskClient


class BackgroundTaskContainer(containers.DeclarativeContainer):
    bg_task_client: Provider[BackgroundTaskClient] = providers.ThreadSafeSingleton(
        HueyBackgroundTaskClient,
    )

    bg_algorithm_runner: Provider[BackgroundAlgorithmRunner] = providers.ThreadSafeSingleton(HueyAlgorithmRunner)
