from __future__ import annotations

from logging import Logger

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from .domain_models import ModelMetadataDomain, ModelSetDomain
from .model_dao import ModelDAO
from .tables import ModelMetadataTable, ModelSetTable


class ModelSetDAO:
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def create(name: str) -> Result[ModelSetDomain, str]:
        modelset = ModelSetTable(name=name)
        try:
            modelset.save()
            return Success(ModelSetDAO.modelset_to_domain(modelset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")

    @staticmethod
    def load(modelset_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = (ModelSetTable.select(ModelSetTable).where(ModelSetTable.id == modelset_id)).get()

            return Success(ModelSetDAO.modelset_to_domain(modelset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def delete(modelset_id: int) -> Result[None, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.id == modelset_id)

            models_to_check = list(modelset.models)

            modelset.delete_instance(True)

            # Check if there are any 'lose' models we need to clean up.
            for model in models_to_check:
                if not model.modelsets.exists():
                    model.delete_instance(True)

            return Success(None)
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def add_model(modelset_id: int, model_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.id == modelset_id)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.id == model_id)

            if model_metadata not in modelset.models:
                modelset.models.add(model_metadata)
                modelset.save()

            return Success(ModelSetDAO.modelset_to_domain(modelset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")

    @staticmethod
    def remove_model(modelset_id: int, model_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.id == modelset_id)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.id == model_id)
            modelset.models.remove(model_metadata)
            modelset.save()
            to_return = ModelSetDAO.modelset_to_domain(modelset)
            through_model = ModelSetTable.models.get_through_model()
            remaining_count = through_model.select().where(through_model.modelmetadatatable == through_model.id).count()

            if remaining_count == 0:
                model_metadata.delete_instance(True)

            return Success(to_return)

        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], str]:
        try:
            modelsets = ModelSetTable.select()
            return Success([ModelSetDAO.modelset_to_domain(m) for m in modelsets])
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def load_all_models(modelset_id: int) -> Result[list[ModelMetadataDomain], str]:
        try:
            modelset = ModelMetadataTable.select().join(ModelSetTable).where(ModelSetTable.id == modelset_id).get()

            print(modelset)

        except Exception as e:
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def modelset_to_domain(modelset: ModelSetTable) -> ModelSetDomain:
        return ModelSetDomain(
            id=modelset.id,
            name=modelset.name,
            models=[ModelDAO.model_to_domain(m) for m in modelset.models],
        )
