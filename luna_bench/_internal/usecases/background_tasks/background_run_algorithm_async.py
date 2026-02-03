from typing import Any

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.background_tasks import BackgroundAlgorithmRunner, BackgroundTaskContainer
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRunAlgorithmAsyncUc
from luna_bench.base_components import BaseAlgorithmAsync


class BackgroundRunAlgorithmAsyncUcImpl(BackgroundRunAlgorithmAsyncUc):
    _bg_algorithm_runner: BackgroundAlgorithmRunner

    @inject
    def __init__(
        self,
        bg_algorithm_runner: BackgroundAlgorithmRunner = Provide[BackgroundTaskContainer.bg_algorithm_runner],
    ) -> None:
        """
        Initialize the BackgroundRunAlgorithmAsyncUc with a background algorithm runner.

        Parameters
        ----------
        bg_algorithm_runner : BackgroundAlgorithmRunner
            The background algorithm runner used to retrieve algorithm results.
        """
        self._bg_algorithm_runner = bg_algorithm_runner

    def __call__(self, algorithm: BaseAlgorithmAsync[Any], model_id: int) -> str:
        return self._bg_algorithm_runner.run_async(algorithm, model_id)  # pragma: no cover
