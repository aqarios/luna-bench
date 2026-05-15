from dependency_injector.wiring import Provide, inject

from luna_bench._internal.background_tasks import BackgroundAlgorithmRunner, BackgroundTaskContainer
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRunAlgorithmSyncUc
from luna_bench.custom import BaseAlgorithmSync


class BackgroundRunAlgorithmSyncUcImpl(BackgroundRunAlgorithmSyncUc):
    _bg_algorithm_runner: BackgroundAlgorithmRunner

    @inject
    def __init__(
        self,
        bg_algorithm_runner: BackgroundAlgorithmRunner = Provide[BackgroundTaskContainer.bg_algorithm_runner],
    ) -> None:
        """
        Initialize the BackgroundRunAlgorithmSyncUc with a background algorithm runner.

        Parameters
        ----------
        bg_algorithm_runner : BackgroundAlgorithmRunner
            The background algorithm runner used to retrieve algorithm results.
        """
        self._bg_algorithm_runner = bg_algorithm_runner

    def __call__(self, algorithm: BaseAlgorithmSync, model_id: int) -> str:
        return self._bg_algorithm_runner.run_sync(algorithm, model_id)  # pragma: no cover
