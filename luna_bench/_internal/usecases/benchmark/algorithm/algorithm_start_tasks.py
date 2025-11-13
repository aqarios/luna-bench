from itertools import product
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from returns.result import Result, Success

from luna_bench._internal.async_tasks.huey_algorithm_runner import HueyAlgorithmRunner
from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import AlgorithmResultDomain, RegisteredDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmStartTasksUc
from luna_bench._internal.user_models import AlgorithmUserModel
from luna_bench._internal.user_models.model_metadata_usermodel import ModelMetadataUserModel
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError

if TYPE_CHECKING:
    from huey.api import Result as HueyResult


class AlgorithmStartTasksUcImpl(AlgorithmStartTasksUc):
    _transaction: DaoTransaction
    _registry_sync: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
    _registry_async: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
    _logger = Logging.get_logger(__name__)

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry_sync: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_sync_registry
        ],
        registry_async: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
    ) -> None:
        """
        Initialize the AlgorithmRunSyncUc with a dao transaction and a registry.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry_sync = registry_sync
        self._registry_async = registry_async

    def __call__(
        self,
        benchmark_name: str,
        models: list[ModelMetadataUserModel],
        algorithms: list[AlgorithmUserModel],
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError]:
        for a, m in product(algorithms, models):
            if m.name in a.results:
                # Skipping already existing results/tasks
                continue

            self._logger.debug(f"Creating job for algorithm {a.name} and model {m.name}")

            task: HueyResult
            if isinstance(a.algorithm, AlgorithmSync):
                task = HueyAlgorithmRunner.run_sync(a.algorithm, m.id)
            elif isinstance(a.algorithm, AlgorithmAsync):
                task = HueyAlgorithmRunner.run_async(a.algorithm, m.id)
            else:
                raise TypeError(type(a))

            result = AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=m.id,
                status=JobStatus.RUNNING,
                error=None,
                task_id=task.id,
                retrival_data=None,
            )
            with self._transaction as t:
                t.algorithm.set_result(benchmark_name=benchmark_name, algorithm_name=a.name, result=result)
            a.results[m.name] = AlgorithmMapper.result_to_user_model(result)
        return Success(None)
