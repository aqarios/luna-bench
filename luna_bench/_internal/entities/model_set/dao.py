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
    def get_model(model_hash: int) -> Result[ModelMetadataDomain, str]:
        try:
            model = ModelMetadataTable.get(ModelMetadataTable.hash == model_hash)
            return Success(ModelSetDAO._model_to_domain(model))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("Model does not exist")

    @staticmethod
    def get_all_models() -> Result[list[ModelMetadataDomain], str]:
        try:
            data = ModelMetadataTable.select()
            return Success([ModelSetDAO._model_to_domain(d) for d in data])
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def get_or_create_model(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, str]:
        try:
            metadata, created = ModelMetadataTable.get_or_create(hash=model_hash, defaults={"name": model_name})

            if created:
                ModelTable.create(model_id=metadata, encoded_model=binary)

            return Success(ModelSetDAO._model_to_domain(metadata))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")
        finally:
            database.commit()

    @staticmethod
    def add_model_to_modelset(modelset_id: int, model_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.id == modelset_id)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.id == model_id)

            if model_metadata not in modelset.models:
                modelset.models.add(model_metadata)
                modelset.save()

            return Success(ModelSetDAO._modelset_to_domain(modelset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("storing failed")

    @staticmethod
    def remove_model_from_modelset(modelset_id: int, model_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.id == modelset_id)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.id == model_id)
            modelset.models.remove(model_metadata)
            modelset.save()
            to_return = ModelSetDAO._modelset_to_domain(modelset)
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
    def load_modelset(modelset_id: int) -> Result[ModelSetDomain, str]:
        try:
            modelset = (ModelSetTable.select(ModelSetTable).where(ModelSetTable.id == modelset_id)).get()

            return Success(ModelSetDAO._modelset_to_domain(modelset))
        except Exception as e:
            raise e
            ModelSetDAO._logger.debug(e)
            return Failure("loading failed")

    @staticmethod
    def delete_modelset(modelset_id: int) -> Result[None, str]:
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
    def load_all_modelsets() -> Result[list[ModelSetDomain], str]:
        try:
            modelsets = ModelSetTable.select()
            return Success([ModelSetDAO._modelset_to_domain(m) for m in modelsets])
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
        return ModelMetadataDomain(id=model.id, name=model.name, hash=model.hash)

    @staticmethod
    def _modelset_to_domain(modelset: ModelSetTable) -> ModelSetDomain:
        return ModelSetDomain(
            id=modelset.id,
            name=modelset.name,
            models=[ModelSetDAO._model_to_domain(m) for m in modelset.models],
        )
