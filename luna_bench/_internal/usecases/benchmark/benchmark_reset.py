from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench.entities.enums import JobStatus

if TYPE_CHECKING:
    from luna_bench.entities import BenchmarkEntity
    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkResetUc


class BenchmarkResetUcImpl(BenchmarkResetUc):
    _transaction: DaoTransaction
    _logger = Logging.get_logger(__name__)

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
        soft: bool = False,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        self._logger.debug(f"Starting {'soft' if soft else 'hard'} reset for benchmark '{benchmark.name}'")

        last_error: DataNotExistError | UnknownLunaBenchError | None = None

        if soft:
            algorithms_to_clear = [
                a.name for a in benchmark.algorithms if any(r.status != JobStatus.DONE for r in a.results.values())
            ]
            features_to_clear = [
                f.name for f in benchmark.features if any(r.status != JobStatus.DONE for r in f.results.values())
            ]
            cascade_metrics = len(algorithms_to_clear) > 0
            metrics_to_clear = [
                m.name
                for m in benchmark.metrics
                if cascade_metrics
                or any(r.status != JobStatus.DONE for inner in m.results.values() for r in inner.values())
            ]
            if not algorithms_to_clear and not features_to_clear and not metrics_to_clear:
                self._logger.debug(f"Soft reset: nothing to clear for benchmark '{benchmark.name}'")
                return Success(None)
        else:
            algorithms_to_clear = [a.name for a in benchmark.algorithms]
            features_to_clear = [f.name for f in benchmark.features]
            metrics_to_clear = [m.name for m in benchmark.metrics]

        self._logger.debug(
            f"Resetting benchmark '{benchmark.name}': {len(algorithms_to_clear)} algorithm(s), "
            f"{len(metrics_to_clear)} metric(s), {len(features_to_clear)} feature(s)"
        )

        with self._transaction as t:
            for name in algorithms_to_clear:
                r = t.algorithm.remove_result(benchmark.name, name)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset algorithm '{name}': {r.failure()}")
                    last_error = r.failure()

            for name in metrics_to_clear:
                r = t.metric.remove_result(benchmark.name, name)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset metric '{name}': {r.failure()}")
                    last_error = r.failure()

            for name in features_to_clear:
                r = t.feature.remove_result(benchmark.name, name)
                if not is_successful(r):
                    self._logger.warning(f"Failed to reset feature '{name}': {r.failure()}")
                    last_error = r.failure()

        if last_error is not None:
            self._logger.debug(f"Reset finished with errors for benchmark '{benchmark.name}'")
            return Failure(last_error)
        self._logger.debug(f"Reset completed for benchmark '{benchmark.name}'")
        return Success(None)
