from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal import HueyConsumer
from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_filter import AlgorithmFilterUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_retrieve_async import AlgorithmRetrieveAsyncUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_retrieve_async_solution import (
    AlgorithmRetrieveAsyncSolutionUcImpl,
)
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_retrieve_sync import AlgorithmRetrieveSyncUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_start_tasks import AlgorithmStartTasksUcImpl
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmRunUc
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError


class AlgorithmRunUcImpl(AlgorithmRunUc):
    _transaction: DaoTransaction
    _registry_sync: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
    _registry_async: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
    _logger = Logging.get_logger(__name__)
    _logger.setLevel("DEBUG")

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
        Initialize the AlgorithmRunUc with a dao transaction and a registry.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        registry : PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
            The registry containing algorithms and their associated data domains.
        """
        self._transaction = transaction
        self._registry_sync = registry_sync
        self._registry_async = registry_async

    def __call__(
        self, benchmark: BenchmarkUserModel, algorithm: AlgorithmUserModel | None = None
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError]:
        result_sync = AlgorithmFilterUcImpl()(benchmark, algorithm_type=AlgorithmType.SYNC, algorithm=algorithm)
        result_async = AlgorithmFilterUcImpl()(benchmark, algorithm_type=AlgorithmType.ASYNC, algorithm=algorithm)

        if not is_successful(result_sync):
            return Failure(result_sync.failure())

        if not is_successful(result_async):
            return Failure(result_async.failure())

        algorithms_sync: list[AlgorithmUserModel] = result_sync.unwrap()
        algorithms_async: list[AlgorithmUserModel] = result_async.unwrap()

        if benchmark.modelset is None:
            self._logger.debug(f"Modelset is missing for benchmark '{benchmark.name}'")
            return Failure(RunModelsetMissingError(benchmark.name))

        #### RUN SUNC AND ASYNC algos
        result_start_async = AlgorithmStartTasksUcImpl()(benchmark.name, benchmark.modelset.models, algorithms_async)
        result_start_sync = AlgorithmStartTasksUcImpl()(benchmark.name, benchmark.modelset.models, algorithms_sync)

        if not is_successful(result_start_async):
            return Failure(result_start_async.failure())
        if not is_successful(result_start_sync):
            return Failure(result_start_sync.failure())

        HueyConsumer.start_consumer()

        AlgorithmRetrieveSyncUcImpl().__call__(benchmark=benchmark)
        AlgorithmRetrieveAsyncUcImpl().__call__(benchmark=benchmark)

        AlgorithmRetrieveAsyncSolutionUcImpl().__call__(benchmark=benchmark)

        HueyConsumer.stop_consumer()

        return Success(None)
