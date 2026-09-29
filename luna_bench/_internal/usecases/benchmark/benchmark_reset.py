from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench.entities.enums import JobStatus, ResetLevel
from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from collections.abc import Callable

    from luna_bench.entities import BenchmarkEntity
    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkResetUc


class BenchmarkResetUcImpl(BenchmarkResetUc):
    _transaction: DaoTransaction
    _logger = BenchLogger.get_logger(__name__)

    @staticmethod
    def _statuses(mode: ResetLevel) -> frozenset[JobStatus] | None:
        """Return the states *mode* clears, or ``None`` when it clears every result.

        Parameters
        ----------
        mode : ResetLevel
            What the reset was asked to clear.

        Returns
        -------
        frozenset[JobStatus] | None
            The states to delete, or ``None`` for all of them.
        """
        match mode:
            case ResetLevel.ALL:
                return None
            case ResetLevel.UNFINISHED:
                return frozenset(s for s in JobStatus if s != JobStatus.DONE)
            case ResetLevel.FAILED:
                return frozenset({JobStatus.FAILED})

    @staticmethod
    def _get_reset_component_names(
        benchmark: BenchmarkEntity,
        mode: ResetLevel,
    ) -> tuple[list[str], list[str], list[str]]:
        """Collect the components holding a result *mode* clears.

        Each component is named because it holds at least one matching result, not
        because all of its results match: which rows go is decided per result when they
        are deleted, so a failed repetition is cleared without the runs that finished
        going with it.

        The metrics computed on a cleared run are removed as well, but they are not
        found here - they are the runs that are gone once the algorithms have been
        cleared, which `_cascade_metrics` deletes afterwards.
        """
        pred: Callable[[JobStatus], bool]
        match mode:
            case ResetLevel.ALL:
                pred = lambda _: True  # noqa: E731
            case ResetLevel.UNFINISHED:
                pred = lambda s: s != JobStatus.DONE  # noqa: E731
            case ResetLevel.FAILED:
                pred = lambda s: s == JobStatus.FAILED  # noqa: E731

        algorithms = [
            a.name for a in benchmark.algorithms if any(pred(r.status) for runs in a.results.values() for r in runs)
        ]
        features = [f.name for f in benchmark.features if any(pred(r.status) for r in f.results.values())]
        metrics = [
            m.name
            for m in benchmark.metrics
            if any(pred(r.status) for inner in m.results.values() for runs in inner.values() for r in runs)
        ]
        return algorithms, features, metrics

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
    ) -> None:
        """Initialize the BenchmarkResetUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def _cascade_metrics(
        self,
        t: DaoTransaction,
        benchmark: BenchmarkEntity,
    ) -> DataNotExistError | UnknownLunaBenchError | None:
        """Drop what every metric computed on a run that has just been cleared.

        Asked of every metric of the benchmark rather than only the ones selected on
        their own status: a metric result is stale because its run is gone, which says
        nothing about the state the result itself is in.

        Parameters
        ----------
        t : DaoTransaction
            The open transaction the results are deleted in.
        benchmark : BenchmarkEntity
            The benchmark being reset.

        Returns
        -------
        DataNotExistError | UnknownLunaBenchError | None
            The last failure, or ``None`` if every metric was cleaned.
        """
        last_error: DataNotExistError | UnknownLunaBenchError | None = None
        for m in benchmark.metrics:
            r = t.metric.remove_orphaned_results(benchmark.name, m.name)
            if not is_successful(r):
                self._logger.warning(f"Failed to reset the results of metric '{m.name}': {r.failure()}")
                last_error = r.failure()
        return last_error

    def __call__(
        self,
        benchmark: BenchmarkEntity,
        *,
        mode: ResetLevel,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        self._logger.debug(f"Starting '{mode}' reset for benchmark '{benchmark.name}'")

        last_error: DataNotExistError | UnknownLunaBenchError | None = None

        algorithms, features, metrics = self._get_reset_component_names(benchmark, mode)
        statuses = self._statuses(mode)

        if not algorithms and not features and not metrics:
            self._logger.debug(f"'{mode}' reset: nothing to clear for benchmark '{benchmark.name}'")
            return Success(None)

        self._logger.debug(
            f"Resetting benchmark '{benchmark.name}': {len(algorithms)} algorithm(s), "
            f"{len(metrics)} metric(s), {len(features)} feature(s)"
        )

        with self._transaction as t:
            for name in algorithms:
                r = t.algorithm.remove_result(benchmark.name, name, statuses)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset algorithm '{name}': {r.failure()}")
                    last_error = r.failure()

            for name in metrics:
                r = t.metric.remove_result(benchmark.name, name, statuses)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset metric '{name}': {r.failure()}")
                    last_error = r.failure()

            if algorithms:
                last_error = self._cascade_metrics(t, benchmark) or last_error

            for name in features:
                r = t.feature.remove_result(benchmark.name, name, statuses)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset feature '{name}': {r.failure()}")
                    last_error = r.failure()

        if last_error is not None:
            self._logger.debug(f"Reset finished with errors for benchmark '{benchmark.name}'")
            return Failure(last_error)
        self._logger.debug(f"Reset completed for benchmark '{benchmark.name}'")
        return Success(None)
