from typing import Any

from luna_quantum import Solution
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.background_tasks import HueyAlgorithmRunner
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRetrieveAlgorithmSyncUc
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BackgroundRetrieveAlgorithmSyncUcImpl(BackgroundRetrieveAlgorithmSyncUc):
    def __call__(
        self, task_id: str
    ) -> Maybe[
        Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]:
        result: Any | None = HueyAlgorithmRunner.retrieve_task_result(task_id)

        if result is not None:
            if not isinstance(result, Result):
                return Some(Failure(UnknownLunaBenchError(ValueError(f"Unexpected result type: {type(result)}"))))

            if not is_successful(result):
                return Some(Failure(result.failure()))
            return Some(Success(result.unwrap()))
        return Nothing
