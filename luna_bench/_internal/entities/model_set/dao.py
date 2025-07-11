from __future__ import annotations

from logging import Logger

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench._internal.shared.database.base_model import database

from .domain_models import ModelMetadataDomain, ModelSetDomain
from .tables import ModelMetadataTable, ModelModelSetTable, ModelSetTable, ModelTable


class ModelSetDAO:
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def create_set(modelset_name: str) -> Result[ModelSetDomain, str]:
        modelset = ModelSetTable(name=modelset_name)
        try:
            modelset.save()
            return Success(ModelSetDAO._modelset_to_domain(modelset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.exception(e)
            return Failure("storing failed")
        finally:
            database.commit()

    @staticmethod
    def create_model(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, str]:
        metadata = ModelMetadataTable(name=model_name, hash=model_hash)

        try:
            metadata.save()
            model = ModelTable(model_id=metadata.model_id, encoded_model=binary)
            model.save()
            return Success(ModelSetDAO._model_to_domain(metadata))
        except Exception as e:
            ModelSetDAO._logger.exception(e)
            return Failure("storing failed")
        finally:
            database.commit()

    @staticmethod
    def add_model_to_modelset(modelset_id: int, model_id: int) -> Result[None, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.modelset_id == modelset_id)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.model_id == model_id)
            ModelModelSetTable.create(model=model_metadata, model_set=modelset)
            return Success(None)
        except Exception as e:
            ModelSetDAO._logger.exception(e)
            return Failure("storing failed")

    @staticmethod
    def load_dataset(dataset_id: int) -> Result[ModelSetDomain, str]:
        try:
            dataset = (
                ModelSetTable.select(ModelSetTable, ModelTable)
                .where(ModelMetadataTable.model_id == dataset_id)
                .join(ModelModelSetTable)
                .join(ModelMetadataTable)
            )
            for row in dataset.namedtuples():
                print(row)
            for d in dataset:
                print(d.name)
                print(d.modelset_id)
                for m in d.models:
                    print(m.model.name)
                    print(m.model.model_id)
                print(d)
                print(d)
                print(d)
                print(d)
                print(d)
                print(d)
            print(dataset.name)
            print(dataset)
            print(dataset.name)
            print(dataset)
            print(dataset)
            print(dataset)
            print(dataset)

            return Success(ModelSetDAO._modelset_to_domain(dataset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.exception(e)
            return Failure("loading failed")

    @staticmethod
    def _model_to_domain(model: ModelMetadataTable) -> ModelMetadataDomain:
        return ModelMetadataDomain(model_id=model.model_id, name=model.name, hash=model.hash)

    @staticmethod
    def _modelset_to_domain(dataset: ModelSetTable) -> ModelSetDomain:
        print(dataset)
        return ModelSetDomain(
            modelset_id=dataset.modelset_id,
            name=dataset.name,
            models=[],
        )
