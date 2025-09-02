from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import Database, _transaction

from luna_bench._internal.dao.protocols import (
    MetricStorage,
    ModelmetricStorage,
    PlotStorage,
    SolveJobStorage,
    StorageTransaction,
)

if TYPE_CHECKING:
    from logging import Logger

    from luna_bench._internal.dao.protocols import BenchmarkStorage, ModelSetStorage, ModelStorage


class PeeweeTransaction(_transaction, StorageTransaction):
    _logger: Logger

    _modelset_storage: ModelSetStorage
    _model_storage: ModelStorage
    _benchmark_storage: BenchmarkStorage
    _metric_storage: MetricStorage
    _modelmetric_storage: ModelmetricStorage
    _solvejob_storage: SolveJobStorage
    _plot_storage: PlotStorage

    def __init__(
        self,
        database: Database,
        modelset_storage: ModelSetStorage,
        model_storage: ModelStorage,
        benchmark_storage: BenchmarkStorage,
        metric_storage: MetricStorage,
        modelmetric_storage: ModelmetricStorage,
        solvejob_storage: SolveJobStorage,
        plot_storage: PlotStorage,
    ) -> None:
        super().__init__(database)
        self._logger = Logging.get_logger(__name__)

        self._modelset_storage = modelset_storage
        self._model_storage = model_storage
        self._benchmark_storage = benchmark_storage
        self._metric_storage = metric_storage
        self._modelmetric_storage = modelmetric_storage
        self._solvejob_storage = solvejob_storage
        self._plot_storage = plot_storage

    @property
    def modelset(self) -> ModelSetStorage:
        return self._modelset_storage

    @property
    def model(self) -> ModelStorage:
        return self._model_storage

    @property
    def benchmark(self) -> BenchmarkStorage:
        return self._benchmark_storage

    @property
    def metric(self) -> MetricStorage:
        return self._metric_storage

    @property
    def model_metric(self) -> ModelmetricStorage:
        return self._modelmetric_storage

    @property
    def solve_job(self) -> SolveJobStorage:
        return self._solvejob_storage

    @property
    def plot(self) -> PlotStorage:
        return self._plot_storage
