from itertools import product

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import AlgorithmResultDomain
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmRunAsBackgroundTasksUc,
    BackgroundRunAlgorithmAsyncUc,
    BackgroundRunAlgorithmSyncUc,
)
from luna_bench.custom import BaseAlgorithmAsync, BaseAlgorithmSync
from luna_bench.entities import AlgorithmEntity, ModelMetadataEntity
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.logging import BenchLogger


class AlgorithmRunAsBackgroundTasksUcImpl(AlgorithmRunAsBackgroundTasksUc):
    _transaction: DaoTransaction
    _logger = BenchLogger.get_logger(__name__)

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
        models: list[ModelMetadataEntity],
        algorithms: list[AlgorithmEntity],
    ) -> None:
        for a, m in product(algorithms, models):
            # One job per repetition. Which repetitions already have a result is what is
            # skipped, rather than the model as a whole: a benchmark that gained
            # repetitions, or one whose failed runs were reset, then queues the runs it is
            # still missing instead of starting over or doing nothing.
            done = {r.repetition for r in a.results.get(m.name, [])}
            for repetition in range(a.repetitions):
                if repetition in done:
                    # Skipping already existing results/tasks
                    continue

                self._queue(benchmark_name, a, m, repetition)

    def _queue(
        self,
        benchmark_name: str,
        a: AlgorithmEntity,
        m: ModelMetadataEntity,
        repetition: int,
    ) -> None:
        """Start one run of an algorithm on one model and record it as running.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the result belongs to.
        a: AlgorithmEntity
            The algorithm to run.
        m: ModelMetadataEntity
            The model to run it on.
        repetition: int
            Which run of the algorithm on this model this is, counted from 0.
        """
        self._logger.debug(f"Creating job for algorithm {a.name} and model {m.name} (repetition {repetition})")

        task_id: str
        if isinstance(a.algorithm, BaseAlgorithmSync):
            task_id = self._background_start_sync(a.algorithm, m.id, a.name)
        elif isinstance(a.algorithm, BaseAlgorithmAsync):
            task_id = self._background_start_async(a.algorithm, m.id, a.name)
        else:  # pragma: no cover This should never happen. There are only two types of algorithms at the moment
            raise TypeError(type(a))

        result = AlgorithmResultDomain.model_construct(
            model_id=m.id,
            repetition=repetition,
            status=JobStatus.RUNNING,
            error=None,
            task_id=task_id,
            retrival_data=None,
        )
        with self._transaction as t:
            t.algorithm.set_result(benchmark_name=benchmark_name, algorithm_name=a.name, result=result)

        runs = a.results.setdefault(m.name, [])
        runs.append(AlgorithmMapper.result_to_user_model(result))
        # Sorted rather than appended to, because a run queued into a gap - repetition 0
        # started again while 1 and 2 are still there - would otherwise land at the end
        # and leave the list in an order a reload does not reproduce.
        runs.sort(key=lambda r: r.repetition)
