from typing import Any

from dependency_injector.wiring import Provide, inject
from luna_model import Solution
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.background_tasks import BackgroundAlgorithmRunner, BackgroundTaskContainer
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRetrieveAlgorithmSyncUc
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BackgroundRetrieveAlgorithmSyncUcImpl(BackgroundRetrieveAlgorithmSyncUc):
    _bg_algorithm_runner: BackgroundAlgorithmRunner

    @inject
    def __init__(
        self,
        bg_algorithm_runner: BackgroundAlgorithmRunner = Provide[BackgroundTaskContainer.bg_algorithm_runner],
    ) -> None:
        """
        Initialize the BackgroundRetrieveAlgorithmSyncUc with a background algorithm runner.

        Parameters
        ----------
        bg_algorithm_runner : BackgroundAlgorithmRunner
            The background algorithm runner used to retrieve algorithm results.
        """
        self._bg_algorithm_runner = bg_algorithm_runner

    def __call__(
        self, task_id: str
    ) -> Maybe[
        Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]:
        result: Any | None = self._bg_algorithm_runner.retrieve_task_result(task_id)

        if result is not None:
            if not isinstance(result, Result):
                return Some(Failure(UnknownLunaBenchError(ValueError(f"Unexpected result type: {type(result)}"))))

            if not is_successful(result):
                return Some(Failure(result.failure()))
            return Some(Success(result.unwrap()))
        return Nothing
