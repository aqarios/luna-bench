from collections import deque
from time import sleep

from dependency_injector.wiring import Provide, inject
from huey.api import partial
from luna_quantum import Logging, Solution
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmRetrieveSyncSolutionsUc,
    BackgroundRetrieveAlgorithmSyncUc,
)
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.configs.config import config
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class AlgorithmRetrieveSyncSolutionsUcImpl(AlgorithmRetrieveSyncSolutionsUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)
    _background_retrieve_sync: BackgroundRetrieveAlgorithmSyncUc

    @inject
    def __init__(
        self,
        background_retrieve_sync: BackgroundRetrieveAlgorithmSyncUc,
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
        self._background_retrieve_sync = background_retrieve_sync

    def _apply_solution(
        self,
        benchmark: BenchmarkUserModel,
        algorithm: AlgorithmUserModel,
        result: AlgorithmResultUserModel,
        s: Solution,
    ) -> Result[
        None,
        ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError,
    ]:
        result.solution = s
        result.status = JobStatus.DONE
        domain_model = AlgorithmMapper.result_to_domain_model(result)
        with self._transaction as t:
            return t.algorithm.set_result(
                benchmark_name=benchmark.name,
                algorithm_name=algorithm.name,
                result=domain_model,
            )

    def _apply_error(
        self,
        benchmark: BenchmarkUserModel,
        algorithm: AlgorithmUserModel,
        result: AlgorithmResultUserModel,
        error: ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        error_msg: str
        if isinstance(error, RunAlgorithmRuntimeError):
            e = error.error()
            error_msg = f"{e.__class__.__name__}: {e}"
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
        self, benchmark: BenchmarkUserModel
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        to_retrieve: deque[tuple[AlgorithmUserModel, AlgorithmResultUserModel]] = deque(
            (a, r)
            for a in benchmark.algorithms
            if isinstance(a.algorithm, AlgorithmSync)
            for r in a.results.values()
            if r.status == JobStatus.RUNNING and r.task_id is not None
        )

        while to_retrieve:
            a, r = to_retrieve.popleft()
            result = self._background_retrieve_sync(r.task_id)  # type: ignore[arg-type] # we know at task_id exists because of the filter before
            if is_successful(result):
                result_applied_solution = (
                    result.unwrap()
                    .bind(partial(self._apply_solution, benchmark, a, r))
                    .lash(partial(self._apply_error, benchmark, a, r))
                )

                if not is_successful(result_applied_solution):
                    return Failure(result_applied_solution.failure())
            else:
                to_retrieve.append((a, r))
            if to_retrieve:
                sleep(config.ALGORITHM_INTERNAL_BACKOFF_TIME)

        return Success(None)
