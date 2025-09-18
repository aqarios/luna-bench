from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from .algorithm_sql_dao import AlgorithmSqlDao
from .benchmark_sql_dao import BenchmarkSqlDao
from .database.peewee_transaction import PeeweeTransaction
from .metric_sql_dao import MetricSqlDao
from .model_sql_dao import ModelSqlDao
from .modelmetric_sql_dao import ModelmetricSqlDao
from .modelset_sql_dao import ModelSetSqlDao
from .plot_sql_dao import PlotSqlDao
from .tables import (
    AlgorithmConfigTable,
    AlgorithmResultTable,
    BenchmarkTable,
    MetricConfigTable,
    MetricResultTable,
    ModelMetadataTable,
    ModelmetricConfigTable,
    ModelmetricResultTable,
    ModelSetTable,
    ModelTable,
    PlotConfigTable,
)
from .tables.base_table import setup_db_proxy

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from luna_bench._internal.dao.protocols import (
        AlgorithmDao,
        BenchmarkDao,
        DaoTransaction,
        MetricDao,
        ModelDao,
        ModelmetricDao,
        ModelSetDao,
        PlotDao,
    )


class DaoContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    model_dao: Provider[ModelDao] = providers.Singleton(ModelSqlDao)
    modelset_dao: Provider[ModelSetDao] = providers.Singleton(ModelSetSqlDao)
    benchmark_dao: Provider[BenchmarkDao] = providers.Singleton(BenchmarkSqlDao)
    modelmetric_dao: Provider[ModelmetricDao] = providers.Singleton(ModelmetricSqlDao)
    metric_dao: Provider[MetricDao] = providers.Singleton(MetricSqlDao)
    algorithm_dao: Provider[AlgorithmDao] = providers.Singleton(AlgorithmSqlDao)
    plot_dao: Provider[PlotDao] = providers.Singleton(PlotSqlDao)

    tables = providers.List(
        BenchmarkTable,
        MetricConfigTable,
        MetricResultTable,
        ModelMetadataTable,
        ModelSetTable,
        ModelTable,
        ModelmetricConfigTable,
        ModelmetricResultTable,
        PlotConfigTable,
        AlgorithmConfigTable,
        AlgorithmResultTable,
        ModelSetTable.models.get_through_model(),
    )

    database = providers.Callable(setup_db_proxy, connection_string=config.DB_CONNECTION_STRING, tables=tables)

    transaction: Provider[DaoTransaction] = providers.Singleton(
        PeeweeTransaction,
        database=database,
        model_storage=model_dao,
        modelset_storage=modelset_dao,
        benchmark_storage=benchmark_dao,
        metric_storage=metric_dao,
        modelmetric_storage=modelmetric_dao,
        solvejob_storage=algorithm_dao,
        plot_storage=plot_dao,
    )
