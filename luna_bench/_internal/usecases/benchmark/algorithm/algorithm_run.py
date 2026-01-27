from dependency_injector.wiring import Provide
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.background_tasks import BackgroundTaskContainer
from luna_bench._internal.background_tasks.protocols import BackgroundTaskClient
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmFilterUc,
    AlgorithmRetrieveAsyncRetrivalDataUc,
    AlgorithmRetrieveAsyncSolutionsUc,
    AlgorithmRetrieveSyncSolutionsUc,
    AlgorithmRunAsBackgroundTasksUc,
    AlgorithmRunUc,
)
from luna_bench.entities import AlgorithmEntity, BenchmarkEntity
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError


class AlgorithmRunUcImpl(AlgorithmRunUc):
    _logger = Logging.get_logger(__name__)
    _algorithm_filter: AlgorithmFilterUc
    _retrieve_sync: AlgorithmRetrieveSyncSolutionsUc
    _retrieve_async_retrieval_data: AlgorithmRetrieveAsyncRetrivalDataUc
    _retrieve_async_solution_data: AlgorithmRetrieveAsyncSolutionsUc
    _start_tasks: AlgorithmRunAsBackgroundTasksUc
    _bg_task_client: BackgroundTaskClient

    def __init__(  # noqa: PLR0913 # Will need to inject the values differently in the future to reduce the complexity
        self,
        algorithm_filter: AlgorithmFilterUc,
        start_tasks: AlgorithmRunAsBackgroundTasksUc,
        retrieve_sync: AlgorithmRetrieveSyncSolutionsUc,
        retrieve_async_retrieval_data: AlgorithmRetrieveAsyncRetrivalDataUc,
        retrieve_async_solution_data: AlgorithmRetrieveAsyncSolutionsUc,
        bg_task_client: BackgroundTaskClient = Provide[BackgroundTaskContainer.bg_task_client],
    ) -> None:
        """
        Initialize the AlgorithmRunUc with a dao transaction and a registry.

        Parameters
        ----------
        algorithm_filter: AlgorithmFilterUc
            UC to filter algorithms by type.
        start_tasks: AlgorithmRunAsBackgroundTasksUc
            UC to start algorithms as background tasks.
        retrieve_sync: AlgorithmRetrieveSyncSolutionsUc
            UC to retrieve solutions for sync algorithms.
        retrieve_async_retrieval_data: AlgorithmRetrieveAsyncRetrivalDataUc
            UC to retrieve retrieval data for async algorithms.
        retrieve_async_solution_data: AlgorithmRetrieveAsyncSolutionsUc
            UC to retrieve solution data for async algorithms.

        """
        self._algorithm_filter = algorithm_filter
        self._start_tasks = start_tasks
        self._retrieve_sync = retrieve_sync
        self._retrieve_async_retrieval_data = retrieve_async_retrieval_data
        self._retrieve_async_solution_data = retrieve_async_solution_data
        self._bg_task_client = bg_task_client

    def __call__(
        self, benchmark: BenchmarkEntity, algorithm: AlgorithmEntity | None = None
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError]:
        result_sync = self._algorithm_filter(benchmark, algorithm_type=AlgorithmType.SYNC, algorithm=algorithm)
        result_async = self._algorithm_filter(benchmark, algorithm_type=AlgorithmType.ASYNC, algorithm=algorithm)

        if not is_successful(result_sync):
            return Failure(result_sync.failure())

        if not is_successful(result_async):
            return Failure(result_async.failure())

        algorithms_sync: list[AlgorithmEntity] = result_sync.unwrap()
        algorithms_async: list[AlgorithmEntity] = result_async.unwrap()

        if benchmark.modelset is None:
            self._logger.debug(f"Modelset is missing for benchmark '{benchmark.name}'")
            return Failure(RunModelsetMissingError(benchmark.name))

        #### RUN SUNC AND ASYNC algos
        self._start_tasks(benchmark.name, benchmark.modelset.models, algorithms_async)
        self._start_tasks(benchmark.name, benchmark.modelset.models, algorithms_sync)

        with self._bg_task_client.consumer():
            self._retrieve_sync(benchmark=benchmark)
            self._retrieve_async_retrieval_data(benchmark=benchmark)

            self._retrieve_async_solution_data(benchmark=benchmark)

        return Success(None)
