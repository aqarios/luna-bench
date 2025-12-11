from typing import Any

from dependency_injector.wiring import Provide, inject
from huey.api import logging
from luna_quantum import Logging, Model, Solution
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.background_tasks.protocols import BackgroundAlgorithmRunner
from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.dao.dao_container import DaoContainer
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .huey_background_task_client import HueyBackgroundTaskClient


class HueyAlgorithmRunner(BackgroundAlgorithmRunner):
    _logger = Logging.get_logger(__name__)

    @staticmethod
    @inject
    def _load_model(
        model_id: int, transaction: DaoTransaction = Provide[DaoContainer.transaction]
    ) -> Result[Model, ModelDecodingError | DataNotExistError | UnknownLunaBenchError]:
        HueyAlgorithmRunner._logger.debug(f"Loading model '{model_id}'.")
        with transaction as t:
            result = t.model.load(model_id)

        if not is_successful(result):
            logging.debug(f"Failed to load model {model_id}")
            return Failure(result.failure())
        model_bytes: bytes = result.unwrap()

        try:
            model = Model.decode(model_bytes)
        except Exception as e:
            logging.debug(f"Failed to decode the model {model_id}")
            return Failure(ModelDecodingError(model_bytes, e))

        return Success(model)

    @staticmethod
    def _run_sync(
        algorithm: AlgorithmSync,
        model_id: int,
    ) -> Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        HueyAlgorithmRunner._logger.info(f"Running algorithm '{algorithm.__class__.__name__}' on model '{model_id}'")

        model = HueyAlgorithmRunner._load_model(model_id)

        if not is_successful(model):
            return Failure(model.failure())

        try:
            return Success(algorithm.run(model.unwrap()))
        except Exception as e:
            return Failure(RunAlgorithmRuntimeError(e))

    @staticmethod
    @HueyBackgroundTaskClient.huey.task()  # type: ignore[misc] # Huey doesn't support type hints
    def _run_sync_huey_task(
        algorithm: AlgorithmSync,
        model_id: int,
    ) -> Result[
        Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError
    ]:  # pragma: no cover
        return HueyAlgorithmRunner._run_sync(algorithm, model_id)

    @staticmethod
    def _run_async[T: BaseModel](
        algorithm: AlgorithmAsync[T],
        model_id: int,
    ) -> Result[T, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        HueyAlgorithmRunner._logger.info(f"Running algorithm {algorithm.__class__.__name__} on model {model_id}")
        model = HueyAlgorithmRunner._load_model(model_id)

        if not is_successful(model):
            return Failure(model.failure())

        try:
            return Success(algorithm.run_async(model.unwrap()))
        except Exception as e:
            return Failure(RunAlgorithmRuntimeError(e))

    @staticmethod
    @HueyBackgroundTaskClient.huey.task()  # type: ignore[misc] # Huey doesn't support type hints
    def _run_async_huey_task[T: BaseModel](
        algorithm: AlgorithmAsync[T],
        model_id: int,
    ) -> Result[
        T, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError
    ]:  # pragma: no cover
        return HueyAlgorithmRunner._run_async(algorithm, model_id)

    @staticmethod
    def run_sync(
        algorithm: AlgorithmSync,
        model_id: int,
    ) -> str:
        return str(
            HueyAlgorithmRunner._run_sync_huey_task(algorithm, model_id).id
        )  # Different type because of the Huey task decorator

    @staticmethod
    def run_async[T: BaseModel](
        algorithm: AlgorithmAsync[T],
        model_id: int,
    ) -> str:
        return str(
            HueyAlgorithmRunner._run_async_huey_task(algorithm, model_id).id
        )  # Different type because of the Huey task decorator

    @staticmethod
    def retrieve_task_result(
        task_id: str,
    ) -> Any | None:  # noqa: ANN401 # We dont know here what type the result of the task has. We don't know what funktion the task was running on.
        return HueyBackgroundTaskClient.huey.result(
            task_id, blocking=False
        )  # pragma: no cover # Hard to cover, it's just a wrapper for an api call so we can mock it more easily.
