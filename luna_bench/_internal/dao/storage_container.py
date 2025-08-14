from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from .database.peewee_transaction import PeeweeTransaction
from .model_dao import ModelDAO
from .modelset_dao import ModelSetDAO
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

    from luna_bench._internal.dao.protocols import ModelSetStorage, ModelStorage, StorageTransaction


class StorageContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    model_storage: Provider[ModelStorage] = providers.Singleton(ModelDAO)
    modelset_storage: Provider[ModelSetStorage] = providers.Singleton(ModelSetDAO)

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
        PeeweeTransaction, database=database, model_storage=model_storage, modelset_storage=modelset_storage
    )
