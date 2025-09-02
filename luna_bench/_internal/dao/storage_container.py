from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from .benchmark_dao import BenchmarkDAO
from .database.peewee_transaction import PeeweeTransaction
from .metric_dao import MetricDAO
from .model_dao import ModelDAO
from .modelmetric_dao import ModelmetricDAO
from .modelset_dao import ModelSetDAO
from .plot_dao import PlotDAO
from .solvejob_dao import SolveJobDAO
from .tables import (
    BenchmarkTable,
    MetricConfigTable,
    MetricResultTable,
    ModelMetadataTable,
    ModelmetricConfigTable,
    ModelmetricResultTable,
    ModelSetTable,
    ModelTable,
    PlotConfigTable,
    SolveJobConfigTable,
    SolveJobResultTable,
)
from .tables.base_table import setup_db_proxy

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from luna_bench._internal.dao.protocols import (
        BenchmarkStorage,
        MetricStorage,
        ModelmetricStorage,
        ModelSetStorage,
        ModelStorage,
        PlotStorage,
        SolveJobStorage,
        StorageTransaction,
    )


class StorageContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    model_storage: Provider[ModelStorage] = providers.Singleton(ModelDAO)
    modelset_storage: Provider[ModelSetStorage] = providers.Singleton(ModelSetDAO)
    benchmark_storage: Provider[BenchmarkStorage] = providers.Singleton(BenchmarkDAO)
    modelmetric_storage: Provider[ModelmetricStorage] = providers.Singleton(ModelmetricDAO)
    metric_storage: Provider[MetricStorage] = providers.Singleton(MetricDAO)
    solvejob_storage: Provider[SolveJobStorage] = providers.Singleton(SolveJobDAO)
    plot_storage: Provider[PlotStorage] = providers.Singleton(PlotDAO)

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
        SolveJobConfigTable,
        SolveJobResultTable,
        ModelSetTable.models.get_through_model(),
    )

    database = providers.Callable(setup_db_proxy, connection_string=config.DB_CONNECTION_STRING, tables=tables)

    transaction: Provider[StorageTransaction] = providers.Singleton(
        PeeweeTransaction,
        database=database,
        model_storage=model_storage,
        modelset_storage=modelset_storage,
        benchmark_storage=benchmark_storage,
        metric_storage=metric_storage,
        modelmetric_storage=modelmetric_storage,
        solvejob_storage=solvejob_storage,
        plot_storage=plot_storage,
    )
