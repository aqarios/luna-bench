from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging, Model, Solution
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces import AlgorithmAsync
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmRetrieveAsyncSolutionUc
from luna_bench._internal.user_models import BenchmarkUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class AlgorithmRetrieveAsyncSolutionUcImpl(AlgorithmRetrieveAsyncSolutionUc):
    _transaction: DaoTransaction
    _registry_async: PydanticRegistry[AlgorithmAsync[BaseModel], RegisteredDataDomain]
    _logger = Logging.get_logger(__name__)
    _logger.setLevel("DEBUG")

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry_async: PydanticRegistry[AlgorithmAsync[BaseModel], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
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
        self._registry_async = registry_async

    def __call__(
        self, benchmark: BenchmarkUserModel
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError]:
        for a in benchmark.algorithms:
            if not isinstance(a.algorithm, AlgorithmAsync):
                continue
            for r in a.results.values():
                if r.status == JobStatus.RUNNING and r.task_id is not None:
                    with self._transaction as t:
                        model = Model.decode(t.model.load(r.model_id).unwrap())

                    result: Solution | str | Result[Solution, str]
                    if r.retrival_data is None:
                        result = "No retrival data provided"
                    else:
                        result = a.algorithm.fetch_result(model, r.retrival_data)
                        result = "No retrival data provided"
                    if not isinstance(result, Result):
                        result = Failure(result) if isinstance(result, str) else Success(result)

                    if is_successful(result):
                        r.solution = result.unwrap()
                        r.status = JobStatus.DONE
                    else:
                        r.status = JobStatus.FAILED
                        r.error = result.failure()

                    domain_model = AlgorithmMapper.result_to_domain_model(r)

                    with self._transaction as t:
                        storage_result = t.algorithm.set_result(
                            benchmark_name=benchmark.name,
                            algorithm_name=a.name,
                            result=domain_model,
                        )
                        if not is_successful(storage_result):
                            return Failure(storage_result.failure())

        return Success(None)
