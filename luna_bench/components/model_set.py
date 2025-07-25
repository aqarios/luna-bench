from __future__ import annotations

from logging import Logger
from typing import ClassVar

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging, Model
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Result

from luna_bench import UsecaseContainer
from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.entities.model_set.modelset_dao import ModelSetDAO
from luna_bench._internal.usecases.modelset import ModelSetAddUc, ModelSetCreateUc
from luna_bench._internal.usecases.modelset.protocols import ModelSetDeleteUc, ModelSetRemoveUc


class ModelData(BaseModel):
    id: int
    model_name: str
    model_hash: int

    @property
    def model(self) -> Model:
        result: Result[bytes, str] = ModelSetDAO.fetch_model(self.model_id)

        if not is_successful(result):
            error = result.failure()
            print(f"Error: {error}")
            raise RuntimeError(error)

        success: bytes = result.unwrap()

        return Model.decode(success)


class ModelSet(BaseModel):
    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    id: int
    name: str
    models: list[ModelData]

    @staticmethod
    @inject
    def create(
        dataset_name: str, modelset_create: ModelSetCreateUc = Provide[UsecaseContainer.modelset_create_uc]
    ) -> ModelSet:
        result: Result[ModelSetDomain, str] = modelset_create(modelset_name=dataset_name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        success: ModelSetDomain = result.unwrap()
        return ModelSet._to_data_set(success)

    @staticmethod
    def load(modelset_id: int) -> ModelSet:
        result: Result[ModelSetDomain, str] = ModelSetDAO.load(modelset_id=modelset_id)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        success: ModelSetDomain = result.unwrap()
        return ModelSet._to_data_set(success)

    @staticmethod
    def load_all() -> list[ModelSet]:
        result: Result[list[ModelSetDomain], str] = ModelSetDAO.load_all()

        if not is_successful(result):
            error = result.failure()
            print(f"Error: {error}")
            raise RuntimeError(error)
        return [ModelSet._to_data_set(m) for m in result.unwrap()]

    @staticmethod
    @inject
    def load_all_models(model_all: ModelSetAddUc = Provide[UsecaseContainer.model_all]) -> Result[list[ModelData], str]:
        result: Result[list[ModelSetDomain], str] = model_all()
        if not is_successful(result):
            error = result.failure()
            print(f"Error: {error}")
            raise RuntimeError(error)
        return [ModelSet._to_model_data(m) for m in result.unwrap()]

    @inject
    def add(self, model: Model, modelset_add: ModelSetAddUc = Provide[UsecaseContainer.modelset_add_uc]) -> None:
        result: Result[ModelSetDomain, str] = modelset_add(dataset_id=self.id, model=model)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    @inject
    def remove(
        self, model: Model, modelset_remove: ModelSetRemoveUc = Provide[UsecaseContainer.modelset_remove_uc]
    ) -> None:
        result: Result[ModelSetDomain, str] = modelset_remove(dataset_id=self.id, model=model)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    @inject
    def delete(self, modelset_delete_uc: ModelSetDeleteUc = Provide[UsecaseContainer.modelset_delete_uc]) -> None:
        result: Result[None, str] = modelset_delete_uc(modelset_id=self.id)

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
