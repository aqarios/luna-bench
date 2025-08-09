from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from luna_bench._internal.entities.database.peewee_transaction import PeeweeTransaction
from luna_bench._internal.entities.model_set import ModelSetDAO
from luna_bench._internal.entities.model_set.model_dao import ModelDAO

from .database.base_model import setup_db_proxy
from .model_set.tables import ModelMetadataTable, ModelSetTable, ModelTable

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from luna_bench._internal.entities.protocols import ModelSetStorage, ModelStorage, StorageTransaction


class StorageContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    model_storage: Provider[ModelStorage] = providers.Singleton(ModelDAO)
    modelset_storage: Provider[ModelSetStorage] = providers.Singleton(ModelSetDAO)

    tables = providers.List(ModelSetTable, ModelMetadataTable, ModelTable, ModelSetTable.models.get_through_model())

    database = providers.Callable(setup_db_proxy, connection_string=config.DB_CONNECTION_STRING, tables=tables)

    transaction: Provider[StorageTransaction] = providers.Singleton(
        PeeweeTransaction, database=database, model_storage=model_storage, modelset_storage=modelset_storage
    )
