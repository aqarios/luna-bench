from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench.errors.data.data_not_exist import DataNotExistError

from .domain_models import ModelMetadataDomain
from .tables import ModelMetadataTable, ModelTable

if TYPE_CHECKING:
    from logging import Logger


class ModelDAO:
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError]:
        try:
            model = ModelMetadataTable.get(ModelMetadataTable.hash == model_hash)
            return Success(ModelDAO.model_to_domain(model))
        except Exception as e:
            ModelDAO._logger.debug(e)
            return Failure(DataNotExistError())

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]:
        data = ModelMetadataTable.select()
        return [ModelDAO.model_to_domain(d) for d in data]

    @staticmethod
    def get_or_create(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, Exception]:
        try:
            metadata, created = ModelMetadataTable.get_or_create(hash=model_hash, defaults={"name": model_name})

            if created:
                ModelTable.create(model_id=metadata, encoded_model=binary)

            return Success(ModelDAO.model_to_domain(metadata))
        except Exception as e:
            ModelDAO._logger.debug(e)
            return Failure(e)

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, Exception]:
        try:
            data = ModelTable.get(ModelTable.model_id == model_id)

            return Success(data.encoded_model)
        except Exception as e:
            ModelDAO._logger.debug(e)
            return Failure(e)

    @staticmethod
    def model_to_domain(model: ModelMetadataTable) -> ModelMetadataDomain:
        return ModelMetadataDomain(id=cast("int", model.id), name=cast("str", model.name), hash=cast("int", model.hash))
