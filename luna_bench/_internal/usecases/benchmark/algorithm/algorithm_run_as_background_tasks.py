from itertools import product

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import AlgorithmResultDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmRunAsBackgroundTasksUc,
    BackgroundRunAlgorithmAsyncUc,
    BackgroundRunAlgorithmSyncUc,
)
from luna_bench._internal.user_models import AlgorithmUserModel
from luna_bench._internal.user_models.model_metadata_usermodel import ModelMetadataUserModel
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync


class AlgorithmRunAsBackgroundTasksUcImpl(AlgorithmRunAsBackgroundTasksUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)

    _background_start_async: BackgroundRunAlgorithmAsyncUc
    _background_start_sync: BackgroundRunAlgorithmSyncUc

    @inject
    def __init__(
        self,
        background_start_async: BackgroundRunAlgorithmAsyncUc,
        background_start_sync: BackgroundRunAlgorithmSyncUc,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
    ) -> None:
        """
        Initialize the AlgorithmRunSyncUc with a dao transaction and a registry.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

        self._background_start_async = background_start_async
        self._background_start_sync = background_start_sync

    def __call__(
        self,
        benchmark_name: str,
        models: list[ModelMetadataUserModel],
        algorithms: list[AlgorithmUserModel],
    ) -> None:
        for a, m in product(algorithms, models):
            if m.name in a.results:
                # Skipping already existing results/tasks
                continue

            self._logger.debug(f"Creating job for algorithm {a.name} and model {m.name}")

            task_id: str
            if isinstance(a.algorithm, BaseAlgorithmSync):
                task_id = self._background_start_sync(a.algorithm, m.id)
            elif isinstance(a.algorithm, BaseAlgorithmAsync):
                task_id = self._background_start_async(a.algorithm, m.id)
            else:  # pragma: no cover This should never happen. There are only two types of algorithms at the moment
                raise TypeError(type(a))

            result = AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=m.id,
                status=JobStatus.RUNNING,
                error=None,
                task_id=task_id,
                retrival_data=None,
            )
            with self._transaction as t:
                t.algorithm.set_result(benchmark_name=benchmark_name, algorithm_name=a.name, result=result)
            a.results[m.name] = AlgorithmMapper.result_to_user_model(result)
