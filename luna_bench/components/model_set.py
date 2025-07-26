from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging, Model
from pydantic import BaseModel
from returns.pipeline import is_successful

from luna_bench._internal import UsecaseContainer
from luna_bench._internal.entities.model_set import ModelDAO
from luna_bench._internal.entities.model_set.modelset_dao import ModelSetDAO

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result

    from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain, ModelSetDomain
    from luna_bench._internal.usecases import ModelAllUc
    from luna_bench._internal.usecases.modelset import ModelSetAddUc, ModelSetCreateUc
    from luna_bench._internal.usecases.modelset.protocols import ModelSetDeleteUc, ModelSetRemoveUc


class ModelData(BaseModel):
    """Metadata about a model."""

    id: int
    model_name: str
    model_hash: int

    @property
    def model(self) -> Model:
        """Fetch the model from the database."""
        result: Result[bytes, Exception] = ModelDAO.fetch_model(self.id)

        if not is_successful(result):
            error = result.failure()
            raise RuntimeError(error)

        success: bytes = result.unwrap()

        return Model.decode(success)


class ModelSet(BaseModel):
    """A set of models."""

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    id: int
    name: str
    models: list[ModelData]

    @staticmethod
    @inject
    def create(
        dataset_name: str, modelset_create: ModelSetCreateUc = Provide[UsecaseContainer.modelset_create_uc]
    ) -> ModelSet:
        """
        A static method to create a new model set using the provided dataset name and a model
        set creation use case. The method ensures the operation is successful and raises
        an exception in case of an error. The successful creation returns an instance
        of `ModelSet`.

        :param dataset_name: The name of the dataset to create the model set for.
        :param modelset_create: The `ModelSetCreateUc` dependency to handle the model set
            creation logic.
        :return: Returns an instance of `ModelSet` representing the successfully created
            model set.
        """
        result: Result[ModelSetDomain, Exception] = modelset_create(modelset_name=dataset_name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        success: ModelSetDomain = result.unwrap()
        return ModelSet._to_data_set(success)

    @staticmethod
    def load(modelset_id: int) -> ModelSet:
        result: Result[ModelSetDomain, Exception] = ModelSetDAO.load(modelset_id=modelset_id)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        success: ModelSetDomain = result.unwrap()
        return ModelSet._to_data_set(success)

    @staticmethod
    def load_all() -> list[ModelSet]:
        result: Result[list[ModelSetDomain], Exception] = ModelSetDAO.load_all()

        if not is_successful(result):
            error = result.failure()
            raise RuntimeError(error)
        return [ModelSet._to_data_set(m) for m in result.unwrap()]

    @staticmethod
    @inject
    def load_all_models(
        model_all: ModelAllUc = Provide[UsecaseContainer.model_all],
    ) -> list[ModelData]:
        return [ModelSet._to_model_data(m) for m in model_all()]

    @inject
    def add(self, model: Model, modelset_add: ModelSetAddUc = Provide[UsecaseContainer.modelset_add_uc]) -> None:
        result: Result[ModelSetDomain, Exception] = modelset_add(dataset_id=self.id, model=model)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    @inject
    def remove(
        self, model: Model, modelset_remove: ModelSetRemoveUc = Provide[UsecaseContainer.modelset_remove_uc]
    ) -> None:
        result: Result[ModelSetDomain, Exception] = modelset_remove(dataset_id=self.id, model=model)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    @inject
    def delete(self, modelset_delete_uc: ModelSetDeleteUc = Provide[UsecaseContainer.modelset_delete_uc]) -> None:
        result: Result[None, Exception] = modelset_delete_uc(modelset_id=self.id)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

    def _update(self, modelset: ModelSetDomain) -> None:
        self.id = modelset.id
        self.name = modelset.name
        self.models = [ModelSet._to_model_data(model=m) for m in modelset.models]

    @staticmethod
    def _to_model_data(model: ModelMetadataDomain) -> ModelData:
        return ModelData(id=model.id, model_name=model.name, model_hash=model.hash)

    @staticmethod
    def _to_data_set(dataset: ModelSetDomain) -> ModelSet:
        return ModelSet(
            id=dataset.id,
            name=dataset.name,
            models=[ModelSet._to_model_data(m) for m in dataset.models],
        )
