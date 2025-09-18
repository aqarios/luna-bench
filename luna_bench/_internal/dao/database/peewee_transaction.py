from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import Database, _transaction

from luna_bench._internal.dao.protocols import (
    AlgorithmDao,
    DaoTransaction,
    MetricDao,
    ModelmetricDao,
    PlotDao,
)

if TYPE_CHECKING:
    from logging import Logger

    from luna_bench._internal.dao.protocols import BenchmarkDao, ModelDao, ModelSetDao


class PeeweeTransaction(_transaction, DaoTransaction):
    _logger: Logger

    _modelset_storage: ModelSetDao
    _model_storage: ModelDao
    _benchmark_storage: BenchmarkDao
    _metric_storage: MetricDao
    _modelmetric_storage: ModelmetricDao
    _solvejob_storage: AlgorithmDao
    _plot_storage: PlotDao

    def __init__(
        self,
        database: Database,
        modelset_storage: ModelSetDao,
        model_storage: ModelDao,
        benchmark_storage: BenchmarkDao,
        metric_storage: MetricDao,
        modelmetric_storage: ModelmetricDao,
        solvejob_storage: AlgorithmDao,
        plot_storage: PlotDao,
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
    def modelset(self) -> ModelSetDao:
        return self._modelset_storage

    @property
    def model(self) -> ModelDao:
        return self._model_storage

    @property
    def benchmark(self) -> BenchmarkDao:
        return self._benchmark_storage

    @property
    def metric(self) -> MetricDao:
        return self._metric_storage

    @property
    def model_metric(self) -> ModelmetricDao:
        return self._modelmetric_storage

    @property
    def algorithm(self) -> AlgorithmDao:
        return self._solvejob_storage

    @property
    def plot(self) -> PlotDao:
        return self._plot_storage
