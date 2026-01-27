from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging, Model, Solution
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmRetrieveAsyncSolutionsUc
from luna_bench.base_components import BaseAlgorithmAsync
from luna_bench.entities import BenchmarkEntity
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class AlgorithmRetrieveAsyncSolutionsUcImpl(AlgorithmRetrieveAsyncSolutionsUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
    ) -> None:
        """
        Initialize the AlgorithmRetrieveAsyncSolutionsUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError]:
        for a in benchmark.algorithms:
            if not isinstance(a.algorithm, BaseAlgorithmAsync):
                continue
            for r in a.results.values():
                if r.status == JobStatus.RUNNING and r.task_id is not None:
                    with self._transaction as t:
                        model = Model.decode(t.model.load(r.model_id).unwrap())

                    result: Solution | str | Result[Solution, str]
                    if r.retrival_data is None:
                        result = Failure("No retrival data provided")
                    else:
                        result = a.algorithm.fetch_result(model, r.retrival_data)
                    if not isinstance(result, Result):
                        result = Failure(result) if isinstance(result, str) else Success(result)

                    if is_successful(result):
                        r.solution = result.unwrap()
                        r.status = JobStatus.DONE
                    else:
                        r.error = result.failure()
                        r.status = JobStatus.FAILED

                    domain_model = AlgorithmMapper.result_to_domain_model(r)

                    with self._transaction as t:
                        storage_result = t.algorithm.set_result(
                            benchmark_name=benchmark.name,
                            algorithm_name=a.name,
                            result=domain_model,
                        )
                        if not is_successful(storage_result):  # pragma: no cover
                            return Failure(storage_result.failure())

        return Success(None)
