from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from . import ModelSetStorage
from .model_dao import ModelDAO
from .tables import ModelMetadataTable, ModelSetTable

if TYPE_CHECKING:
    from logging import Logger


class ModelSetDAO(ModelSetStorage):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def create(modelset_name: str) -> Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]:
        modelset = ModelSetTable(name=modelset_name)
        try:
            modelset.save()
            return Success(ModelSetDAO.modelset_to_domain(modelset))

        except IntegrityError:
            return Failure(DataNotUniqueError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(modelset_name: str) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            modelset = (ModelSetTable.select(ModelSetTable).where(ModelSetTable.name == modelset_name)).get()

            return Success(ModelSetDAO.modelset_to_domain(modelset))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            ModelSetDAO._logger.debug(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def delete(modelset_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)

            models_to_check = list(modelset.models)

            modelset.delete_instance(recursive=True)

            # Check if there are any 'lose' models we need to clean up.
            for model in models_to_check:
                if not model.modelsets.exists():
                    model.delete_instance(recursive=True)

            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            ModelSetDAO._logger.debug(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def add_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.id == model_id)

            if model_metadata not in modelset.models:
                modelset.models.add(model_metadata)
                modelset.save()

            return Success(ModelSetDAO.modelset_to_domain(modelset))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            ModelSetDAO._logger.debug(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)
            model_metadata = ModelMetadataTable.get(ModelMetadataTable.id == model_id)
            modelset.models.remove(model_metadata)
            modelset.save()
            to_return = ModelSetDAO.modelset_to_domain(modelset)
            through_model = ModelSetTable.models.get_through_model()
            remaining_count = through_model.select().where(through_model.modelmetadatatable == through_model.id).count()

            if remaining_count == 0:
                model_metadata.delete_instance(recursive=True)

            return Success(to_return)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            ModelSetDAO._logger.debug(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], UnknownLunaBenchError]:
        try:
            modelsets = ModelSetTable.select()
            return Success([ModelSetDAO.modelset_to_domain(m) for m in modelsets])
        except Exception as e:  # pragma: no cover
            ModelSetDAO._logger.debug(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load_all_models(
        modelset_name: str,
    ) -> Result[list[ModelMetadataDomain], DataNotExistError | UnknownLunaBenchError]:
        try:
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)

            return Success([ModelDAO.model_to_domain(m) for m in modelset.models])
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            ModelSetDAO._logger.debug(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def modelset_to_domain(modelset: ModelSetTable) -> ModelSetDomain:
        return ModelSetDomain(
            id=cast("int", modelset.id),
            name=cast("str", modelset.name),
            models=[ModelDAO.model_to_domain(m) for m in modelset.models],
        )
