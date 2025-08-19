from dependency_injector import containers, providers
from dependency_injector.providers import Configuration, Provider

from luna_bench._internal.dao import StorageContainer

from .models import ModelAllUc, ModelAllUcImpl
from .models.model_fetch import ModelFetchUcImpl
from .models.protocols import ModelFetchUc
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
from .modelset.modelset_load import ModelSetLoadUcImpl
from .modelset.modelset_load_all import ModelSetLoadAllUcImpl
from .modelset.protocols import ModelSetLoadAllUc, ModelSetLoadUc


class UsecaseContainer(containers.DeclarativeContainer):
    config: Configuration = providers.Configuration()

    storage_container = providers.Container(StorageContainer, config=config)

    # ModelSet usecases
    modelset_create_uc: Provider[ModelSetCreateUc] = providers.Singleton(
        ModelSetCreateUcImpl, transaction=storage_container.transaction
    )
    modelset_load_uc: Provider[ModelSetLoadUc] = providers.Singleton(
        ModelSetLoadUcImpl, transaction=storage_container.transaction
    )
    modelset_load_all_uc: Provider[ModelSetLoadAllUc] = providers.Singleton(
        ModelSetLoadAllUcImpl, transaction=storage_container.transaction
    )

    modelset_add_uc: Provider[ModelSetAddUc] = providers.Singleton(
        ModelSetAddUcImpl, transaction=storage_container.transaction
    )
    modelset_remove_uc: Provider[ModelSetRemoveUc] = providers.Singleton(
        ModelSetRemoveUcImpl, transaction=storage_container.transaction
    )
    modelset_delete_uc: Provider[ModelSetDeleteUc] = providers.Singleton(
        ModelSetDeleteUcImpl, transaction=storage_container.transaction
    )

    # Model usecases
    model_all_uc: Provider[ModelAllUc] = providers.Singleton(ModelAllUcImpl, transaction=storage_container.transaction)

    model_fetch_uc: Provider[ModelFetchUc] = providers.Singleton(
        ModelFetchUcImpl, transaction=storage_container.transaction
    )
