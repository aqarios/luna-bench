from dependency_injector import containers, providers
from dependency_injector.providers import Configuration

from luna_bench._internal.entities.storage_container import StorageContainer

from .models import ModelAllUc, ModelAllUcImpl
from .modelset import (
    ModelSetAddUc,
    ModelSetAddUcImpl,
    ModelSetCreateUc,
    ModelSetCreateUcImpl,
    ModelSetDeleteUc,
    ModelSetDeleteUcImpl,
    ModelSetRemoveUc,
    ModelSetRemoveUcImpl,
)


class UsecaseContainer(containers.DeclarativeContainer):
    config: Configuration = providers.Configuration()

    storage_container = providers.Container(StorageContainer, config=config)

    modelset_create_uc: ModelSetCreateUc = providers.Singleton(
        ModelSetCreateUcImpl, transaction=storage_container.transaction
    )

    modelset_add_uc: ModelSetAddUc = providers.Singleton(ModelSetAddUcImpl, transaction=storage_container.transaction)
    modelset_remove_uc: ModelSetRemoveUc = providers.Singleton(
        ModelSetRemoveUcImpl, transaction=storage_container.transaction
    )
    modelset_delete_uc: ModelSetDeleteUc = providers.Singleton(
        ModelSetDeleteUcImpl, transaction=storage_container.transaction
    )

    model_all: ModelAllUc = providers.Singleton(ModelAllUcImpl, transaction=storage_container.transaction)
