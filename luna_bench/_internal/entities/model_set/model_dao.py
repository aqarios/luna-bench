from __future__ import annotations

from logging import Logger

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from .domain_models import ModelMetadataDomain
from .tables import ModelMetadataTable, ModelTable


class ModelDAO:
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, str]:
        try:
            model = ModelMetadataTable.get(ModelMetadataTable.hash == model_hash)
            return Success(ModelDAO.model_to_domain(model))
        except Exception as e:
            raise e
            ModelDAO._logger.debug(e)
            return Failure("Model does not exist")

    @staticmethod
    def get_all() -> Result[list[ModelMetadataDomain], str]:
        try:
            data = ModelMetadataTable.select()
            return Success([ModelDAO.model_to_domain(d) for d in data])
        except Exception as e:
            raise e
            ModelDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def get_or_create(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, str]:
        try:
            metadata, created = ModelMetadataTable.get_or_create(hash=model_hash, defaults={"name": model_name})

            if created:
                ModelTable.create(model_id=metadata, encoded_model=binary)

            return Success(ModelDAO.model_to_domain(metadata))
        except Exception as e:
            raise e
            ModelDAO._logger.debug(e)
            return Failure("storing failed")

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, str]:
        try:
            data = ModelTable.get(ModelTable.model_id == model_id)

            return Success(data.encoded_model)
        except Exception as e:
            raise e
            ModelDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def model_to_domain(model: ModelMetadataTable) -> ModelMetadataDomain:
        return ModelMetadataDomain(id=model.id, name=model.name, hash=model.hash)
