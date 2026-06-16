from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench.entities.enums import JobStatus, ResetLevel

if TYPE_CHECKING:
    from collections.abc import Callable

    from luna_bench.entities import BenchmarkEntity
    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkResetUc


class BenchmarkResetUcImpl(BenchmarkResetUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)

    @staticmethod
    def _get_reset_component_names(
        benchmark: BenchmarkEntity,
        mode: ResetLevel,
    ) -> tuple[list[str], list[str], list[str]]:
        """Collect component names to clear based on *mode*.

        Metrics are cascaded: whenever any algorithm result is included,
        all metric results are included (since metrics depend on algorithm
        outputs).
        """
        pred: Callable[[JobStatus], bool]
        match mode:
            case ResetLevel.ALL:
                pred = lambda _: True  # noqa: E731
            case ResetLevel.UNFINISHED:
                pred = lambda s: s != JobStatus.DONE  # noqa: E731
            case ResetLevel.FAILED:
                pred = lambda s: s == JobStatus.FAILED  # noqa: E731

        algorithms = [a.name for a in benchmark.algorithms if any(pred(r.status) for r in a.results.values())]
        features = [f.name for f in benchmark.features if any(pred(r.status) for r in f.results.values())]
        cascade_metrics = len(algorithms) > 0
        metrics = [
            m.name
            for m in benchmark.metrics
            if cascade_metrics or any(pred(r.status) for inner in m.results.values() for r in inner.values())
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

    def __call__(
        self,
        benchmark: BenchmarkEntity,
        *,
        mode: ResetLevel,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        self._logger.debug(f"Starting '{mode}' reset for benchmark '{benchmark.name}'")

        last_error: DataNotExistError | UnknownLunaBenchError | None = None

        algorithms, features, metrics = self._get_reset_component_names(benchmark, mode)

        if not algorithms and not features and not metrics:
            self._logger.debug(f"'{mode}' reset: nothing to clear for benchmark '{benchmark.name}'")
            return Success(None)

        self._logger.debug(
            f"Resetting benchmark '{benchmark.name}': {len(algorithms)} algorithm(s), "
            f"{len(metrics)} metric(s), {len(features)} feature(s)"
        )

        with self._transaction as t:
            for name in algorithms:
                r = t.algorithm.remove_result(benchmark.name, name)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset algorithm '{name}': {r.failure()}")
                    last_error = r.failure()

            for name in metrics:
                r = t.metric.remove_result(benchmark.name, name)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset metric '{name}': {r.failure()}")
                    last_error = r.failure()

            for name in features:
                r = t.feature.remove_result(benchmark.name, name)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset feature '{name}': {r.failure()}")
                    last_error = r.failure()

        if last_error is not None:
            self._logger.debug(f"Reset finished with errors for benchmark '{benchmark.name}'")
            return Failure(last_error)
        self._logger.debug(f"Reset completed for benchmark '{benchmark.name}'")
        return Success(None)
