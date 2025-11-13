from collections import deque
from functools import partial
from time import sleep
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.async_tasks.huey_algorithm_runner import HueyAlgorithmRunner
from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmRetrieveAsyncUc
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.configs.config import config
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from returns.maybe import Maybe


class AlgorithmRetrieveAsyncUcImpl(AlgorithmRetrieveAsyncUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
    ) -> None:
        """
        Initialize the AlgorithmRunUc with a dao transaction and a registry.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        registry : PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
            The registry containing algorithms and their associated data domains.
        """
        self._transaction = transaction

    def _apply_async_retrival_data(
        self,
        benchmark: BenchmarkUserModel,
        algorithm: AlgorithmUserModel,
        result: AlgorithmResultUserModel,
        retrival_data: BaseModel,
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        try:
            result.retrival_data = ArbitraryDataDomain.model_validate(retrival_data.model_dump())
        except ValidationError as e:
            return Failure(UnknownLunaBenchError(e))
        result.status = JobStatus.RUNNING
        domain_model = AlgorithmMapper.result_to_domain_model(result)
        with self._transaction as t:
            return t.algorithm.set_result(
                benchmark_name=benchmark.name,
                algorithm_name=algorithm.name,
                result=domain_model,
            )

    def __call__(
        self, benchmark: BenchmarkUserModel
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        to_retrieve: deque[tuple[AlgorithmUserModel, AlgorithmResultUserModel]] = deque(
            (a, r)
            for a in benchmark.algorithms
            if isinstance(a.algorithm, AlgorithmAsync)
            for r in a.results.values()
            if r.status == JobStatus.RUNNING and r.task_id is not None
        )

        while to_retrieve:
            a, r = to_retrieve.popleft()
            if r.task_id is None:
                return Failure(UnknownLunaBenchError(ValueError()))
            result: Maybe[
                Result[
                    BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError
                ]
            ] = HueyAlgorithmRunner.retrieve_async(r.task_id)
            if is_successful(result):
                result_applied_solution = result.unwrap().bind(
                    partial(self._apply_async_retrival_data, benchmark, a, r)
                )

                if not is_successful(result_applied_solution):
                    return Failure(result_applied_solution.failure())

            else:
                to_retrieve.append((a, r))
            if to_retrieve:
                sleep(config.ALGORITHM_INTERNAL_BACKOFF_TIME)

        return Success(None)
