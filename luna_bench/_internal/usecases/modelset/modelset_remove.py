from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain, StorageTransaction


class ModelSetRemoveUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, Exception]:
        with self.transaction as t:
            get_result: Result[ModelMetadataDomain, Exception] = t.model.get(model_hash=model.__hash__())

            if not is_successful(get_result):
                return Failure(get_result.failure())

            result: Result[ModelSetDomain, Exception] = t.modelset.remove_model(
                modelset_id=dataset_id, model_id=get_result.unwrap().id
            )
            return result
