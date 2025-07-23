from dependency_injector import containers, providers

from luna_bench._internal.shared.database.transactions.peewee_transaction import PeeweeTransaction
from luna_bench._internal.shared.database.transactions.storage_transaction import StorageTransaction
from luna_bench._internal.usecases.models.model_all import ModelAllUcImpl
from luna_bench._internal.usecases.models.protocols import ModelAllUc
from luna_bench._internal.usecases.modelset import ModelSetAddUc, ModelSetCreateUc
from luna_bench._internal.usecases.modelset.modelset_add import ModelSetAddUcImpl
from luna_bench._internal.usecases.modelset.modelset_create import ModelSetCreateUcImpl
from luna_bench._internal.usecases.modelset.modelset_delete import ModelSetDeleteUcImpl
from luna_bench._internal.usecases.modelset.modelset_remove import ModelSetRemoveUcImpl
from luna_bench._internal.usecases.modelset.protocols import ModelSetDeleteUc, ModelSetRemoveUc


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    storage_transaction: StorageTransaction = providers.Singleton(PeeweeTransaction)

    modelset_create_uc: ModelSetCreateUc = providers.Singleton(
        ModelSetCreateUcImpl, storage_transaction=storage_transaction
    )

    modelset_add_uc: ModelSetAddUc = providers.Singleton(ModelSetAddUcImpl, storage_transaction=storage_transaction)
    modelset_remove_uc: ModelSetRemoveUc = providers.Singleton(
        ModelSetRemoveUcImpl, storage_transaction=storage_transaction
    )
    modelset_delete_uc: ModelSetDeleteUc = providers.Singleton(
        ModelSetDeleteUcImpl, storage_transaction=storage_transaction
    )

    model_all: ModelAllUc = providers.Singleton(ModelAllUcImpl, storage_transaction=storage_transaction)
