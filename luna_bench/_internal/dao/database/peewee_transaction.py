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

    _modelset_dao: ModelSetDao
    _model_dao: ModelDao
    _benchmark_dao: BenchmarkDao
    _metric_dao: MetricDao
    _modelmetric_dao: ModelmetricDao
    _solvejob_dao: AlgorithmDao
    _plot_dao: PlotDao

    def __init__(
        self,
        database: Database,
        modelset_dao: ModelSetDao,
        model_dao: ModelDao,
        benchmark_dao: BenchmarkDao,
        metric_dao: MetricDao,
        modelmetric_dao: ModelmetricDao,
        solvejob_dao: AlgorithmDao,
        plot_dao: PlotDao,
    ) -> None:
        super().__init__(database)
        self._logger = Logging.get_logger(__name__)

        self._modelset_dao = modelset_dao
        self._model_dao = model_dao
        self._benchmark_dao = benchmark_dao
        self._metric_dao = metric_dao
        self._modelmetric_dao = modelmetric_dao
        self._solvejob_dao = solvejob_dao
        self._plot_dao = plot_dao

    @property
    def modelset(self) -> ModelSetDao:
        return self._modelset_dao

    @property
    def model(self) -> ModelDao:
        return self._model_dao

    @property
    def benchmark(self) -> BenchmarkDao:
        return self._benchmark_dao

    @property
    def metric(self) -> MetricDao:
        return self._metric_dao

    @property
    def model_metric(self) -> ModelmetricDao:
        return self._modelmetric_dao

    @property
    def algorithm(self) -> AlgorithmDao:
        return self._solvejob_dao

    @property
    def plot(self) -> PlotDao:
        return self._plot_dao
