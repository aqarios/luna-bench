from collections import deque
from functools import partial
from time import sleep
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmRetrieveAsyncRetrivalDataUc,
    BackgroundRetrieveAlgorithmAsyncUc,
)
from luna_bench.configs.config import config
from luna_bench.custom import BaseAlgorithmAsync
from luna_bench.entities import AlgorithmEntity, AlgorithmResultEntity, BenchmarkEntity
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from returns.maybe import Maybe


class AlgorithmRetrieveAsyncRetrivalDataUcImpl(AlgorithmRetrieveAsyncRetrivalDataUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)
    _background_retrieve_async: BackgroundRetrieveAlgorithmAsyncUc

    @inject
    def __init__(
        self,
        background_retrieve_async: BackgroundRetrieveAlgorithmAsyncUc,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
    ) -> None:
        """
        Initialize the AlgorithmRunUc with a dao transaction and a registry.

        Parameters
        ----------
        background_retrieve_async : BackgroundRetrieveAlgorithmAsyncUc
            The retrieval algorithm for async solutions.
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._background_retrieve_async = background_retrieve_async

    def _apply_async_retrival_data(
        self,
        benchmark: BenchmarkEntity,
        algorithm: AlgorithmEntity,
        result: AlgorithmResultEntity,
        retrival_data: BaseModel,
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        try:
            result.retrival_data = ArbitraryDataDomain.model_validate(retrival_data.model_dump())
        except (AttributeError, ValidationError) as e:
            return Failure(UnknownLunaBenchError(e))
        result.status = JobStatus.RUNNING
        domain_model = AlgorithmMapper.result_to_domain_model(result)
        with self._transaction as t:
            return t.algorithm.set_result(
                benchmark_name=benchmark.name,
                algorithm_name=algorithm.name,
                result=domain_model,
            )

    def _apply_error(
        self,
        benchmark: BenchmarkEntity,
        algorithm: AlgorithmEntity,
        result: AlgorithmResultEntity,
        error: ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        error_msg: str
        if isinstance(error, (RunAlgorithmRuntimeError, UnknownLunaBenchError)):
            e = error.error()
            error_msg = f"{error.__class__.__name__} with: {e.__class__.__name__}: {e}"
        else:
            error_msg = f"{error.__class__.__name__}: {error}"
        result.solution = None
        result.status = JobStatus.FAILED
        result.error = error_msg
        domain_model = AlgorithmMapper.result_to_domain_model(result)
        with self._transaction as t:
            return t.algorithm.set_result(
                benchmark_name=benchmark.name,
                algorithm_name=algorithm.name,
                result=domain_model,
            )

    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        to_retrieve: deque[tuple[AlgorithmEntity, AlgorithmResultEntity]] = deque(
            (a, r)
            for a in benchmark.algorithms
            if isinstance(a.algorithm, BaseAlgorithmAsync)
            for r in a.results.values()
            if r.status == JobStatus.RUNNING and r.task_id is not None
        )

        while to_retrieve:
            a, r = to_retrieve.popleft()

            result: Maybe[
                Result[
                    BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError
                ]
            ] = self._background_retrieve_async(r.task_id)  # type: ignore[arg-type] # we know at task_id exists because of the filter before
            if is_successful(result):
                result_applied_solution = (
                    result.unwrap()
                    .bind(partial(self._apply_async_retrival_data, benchmark, a, r))
                    .lash(partial(self._apply_error, benchmark, a, r))
                )

                if not is_successful(result_applied_solution):
                    return Failure(result_applied_solution.failure())
            else:
                to_retrieve.append((a, r))
            if to_retrieve:
                sleep(config.LB_ALGORITHM_INTERNAL_BACKOFF_TIME)

        return Success(None)
