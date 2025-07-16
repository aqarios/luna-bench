from __future__ import annotations

from logging import Logger

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench._internal.shared.database.base_model import database

from .domain_models import ModelMetadataDomain, ModelSetDomain
from .tables import ModelMetadataTable, ModelSetTable, ModelTable


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
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")
        finally:
            database.commit()

    @staticmethod
    def create_model(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, str]:
        metadata = ModelMetadataTable(name=model_name, hash=model_hash)

        try:
            metadata.save()
            print(metadata.model_id)
            model = ModelTable(model_id=metadata, encoded_model=binary)
            model.save()
            return Success(ModelSetDAO._model_to_domain(metadata))
        except Exception as e:
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")
        finally:
            database.commit()

    @staticmethod
    def add_model_to_modelset(modelset_id: int, model_id: int) -> Result[None, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.modelset_id == modelset_id)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.model_id == model_id)
            modelset.models.add(model_metadata)
            modelset.save()
            return Success(None)
        except Exception as e:
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")

    @staticmethod
    def load_modelset(modelset_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = (
                ModelSetTable.select(ModelSetTable)
                .where(ModelSetTable.modelset_id == modelset_id)
            ).get()

            return Success(ModelSetDAO._modelset_to_domain(modelset))
        except Exception as e:
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, str]:
        try:
            data = ModelTable.get(ModelTable.model_id == model_id)

            return Success(data.encoded_model)
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def _model_to_domain(model: ModelMetadataTable) -> ModelMetadataDomain:
        return ModelMetadataDomain(model_id=model.model_id, name=model.name, hash=model.hash)

    @staticmethod
    def _modelset_to_domain(modelset: ModelSetTable) -> ModelSetDomain:
        return ModelSetDomain(
            modelset_id=modelset.modelset_id,
            name=modelset.name,
            models=[ModelSetDAO._model_to_domain(m)for m in modelset.models],
        )
