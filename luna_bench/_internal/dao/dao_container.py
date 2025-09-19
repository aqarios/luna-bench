from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from .algorithm_sql_dao import AlgorithmSqlDao
from .benchmark_sql_dao import BenchmarkSqlDao
from .database.peewee_transaction import PeeweeTransaction
from .feature_sql_dao import FeatureSqlDao
from .metric_sql_dao import MetricSqlDao
from .model_sql_dao import ModelSqlDao
from .modelset_sql_dao import ModelSetSqlDao
from .plot_sql_dao import PlotSqlDao
from .tables import (
    AlgorithmResultTable,
    AlgorithmTable,
    BenchmarkTable,
    FeatureResultTable,
    FeatureTable,
    MetricResultTable,
    MetricTable,
    ModelMetadataTable,
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
        FeatureDao,
        MetricDao,
        ModelDao,
        ModelSetDao,
        PlotDao,
    )


class DaoContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    model_dao: Provider[ModelDao] = providers.Singleton(ModelSqlDao)
    modelset_dao: Provider[ModelSetDao] = providers.Singleton(ModelSetSqlDao)
    benchmark_dao: Provider[BenchmarkDao] = providers.Singleton(BenchmarkSqlDao)
    feature_dao: Provider[FeatureDao] = providers.Singleton(FeatureSqlDao)
    metric_dao: Provider[MetricDao] = providers.Singleton(MetricSqlDao)
    algorithm_dao: Provider[AlgorithmDao] = providers.Singleton(AlgorithmSqlDao)
    plot_dao: Provider[PlotDao] = providers.Singleton(PlotSqlDao)

    tables = providers.List(
        BenchmarkTable,
        MetricTable,
        MetricResultTable,
        ModelMetadataTable,
        ModelSetTable,
        ModelTable,
        FeatureTable,
        FeatureResultTable,
        PlotConfigTable,
        AlgorithmTable,
        AlgorithmResultTable,
        ModelSetTable.models.get_through_model(),  # type: ignore[no-untyped-call]
    )

    database = providers.Callable(setup_db_proxy, connection_string=config.DB_CONNECTION_STRING, tables=tables)

    transaction: Provider[DaoTransaction] = providers.Singleton(
        PeeweeTransaction,
        database=database,
        model_dao=model_dao,
        modelset_dao=modelset_dao,
        benchmark_dao=benchmark_dao,
        metric_dao=metric_dao,
        feature_dao=feature_dao,
        solvejob_dao=algorithm_dao,
        plot_dao=plot_dao,
    )
