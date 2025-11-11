from typing import Any

from dependency_injector.wiring import Provide, inject
from huey.api import logging
from luna_quantum import Logging, Model, Solution
from pydantic import BaseModel
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.async_tasks.huey_consumer import HueyConsumer
from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.dao.dao_container import DaoContainer
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class HueyAlgorithmRunner:
    _logger = Logging.get_logger(__name__)
    _logger.setLevel("DEBUG")

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
    @HueyConsumer.huey.task()  # type: ignore[misc] # Huey doesn't support type hints
    def run_sync(
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
    @HueyConsumer.huey.task()  # type: ignore[misc] # Huey doesn't support type hints
    def run_async[T: BaseModel](
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
    def retrieve_sync(
        task_id: str,
    ) -> Maybe[
        Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]:
        result: Any | None = HueyConsumer.huey.result(task_id, blocking=False)

        if result is not None:
            if not isinstance(result, Result):
                return Some(Failure(UnknownLunaBenchError(ValueError(f"Unexpected result type: {type(result)}"))))

            if not is_successful(result):
                return Some(Failure(result.failure()))
            return Some(Success(result.unwrap()))
        return Nothing

    @staticmethod
    def retrieve_async(
        task_id: str,
    ) -> Maybe[
        Result[BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]:
        result: Any | None = HueyConsumer.huey.result(task_id, blocking=False)
        if result is not None:
            if not isinstance(result, Result):
                raise ValueError

            if not is_successful(result):
                return Some(Failure(result.failure()))
            return Some(Success(result.unwrap()))
        return Nothing
