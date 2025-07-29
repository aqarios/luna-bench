from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging, Model
from pydantic import BaseModel
from returns.pipeline import is_successful

from luna_bench._internal import UsecaseContainer
from luna_bench._internal.entities.model_set import ModelDAO
from luna_bench._internal.entities.model_set.modelset_dao import ModelSetDAO
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result

    from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain, ModelSetDomain
    from luna_bench._internal.usecases import ModelAllUc
    from luna_bench._internal.usecases.modelset import ModelSetAddUc, ModelSetCreateUc
    from luna_bench._internal.usecases.modelset.protocols import ModelSetDeleteUc, ModelSetRemoveUc


class ModelData(BaseModel):
    """
    Metadata for a model.

    A class that stores essential metadata about a model, including its ID,
    name, and hash value. Provides also access to the actual model.

    Attributes
    ----------
    id : int
        The unique identifier for the model.
    model_name : str
        The name of the model.
    model_hash : int
        The hash value of the model, used for identification and verification.
    """

    id: int
    model_name: str
    model_hash: int

    @property
    def model(self) -> Model:
        """
        Fetch the model from the database.

        Retrieves the model from the database using the model ID, decodes it, and returns a Model object.

        Returns
        -------
        Model
            The decoded model object.

        Raises
        ------
        RuntimeError
            If the model cannot be fetched from the database.
        """
        result: Result[bytes, Exception] = ModelDAO.fetch_model(self.id)

        if not is_successful(result):
            error = result.failure()
            raise RuntimeError(error)

        success: bytes = result.unwrap()

        return Model.decode(success)


class ModelSet(BaseModel):
    """
    Set of models.

    Represents a collection of models with operations for creating, loading, adding,
    removing, and deleting models.

    Attributes
    ----------
    id : int
        The unique identifier for the model set.
    name : str
        The name of the model set.
    models : list[ModelData]
        A list of ModelData objects representing the models in this set.
    """

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
        Create a new model set with the given dataset name.

        Creates a new model set using the provided dataset name and a model
        set creation use case.

        Parameters
        ----------
        dataset_name : str
            The name of the dataset.
        modelset_create : ModelSetCreateUc, injected
            The use case for creating model sets, by default, it's provided by dependency injection.

        Returns
        -------
        ModelSet
            An instance of ModelSet representing the successfully created model set.
        """
        result: Result[ModelSetDomain, DataNotUniqueError | Exception] = modelset_create(modelset_name=dataset_name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        success: ModelSetDomain = result.unwrap()
        return ModelSet._to_data_set(success)

    @staticmethod
    def load(modelset_id: int) -> ModelSet:
        """
        Load a model set by its ID.

        Retrieves a model set from the database using its unique identifier.

        Parameters
        ----------
        modelset_id : int
            The unique identifier of the model set to load.

        Returns
        -------
        ModelSet
            The loaded model set.
        """
        result: Result[ModelSetDomain, Exception] = ModelSetDAO.load(modelset_id=modelset_id)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        success: ModelSetDomain = result.unwrap()
        return ModelSet._to_data_set(success)

    @staticmethod
    def load_all() -> list[ModelSet]:
        """
        Load all model sets from the database.

        Retrieves all model sets stored in the database.

        Returns
        -------
        list[ModelSet]
            A list of all model sets.
        """
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
        """
        Load all models from the database.

        Retrieves all models stored in the database, regardless of which model set they belong to.

        Parameters
        ----------
        model_all : ModelAllUc, injected
            The use case for retrieving all models, by default provided by dependency injection.

        Returns
        -------
        list[ModelData]
            A list of ModelData objects representing all models in the database.
        """
        return [ModelSet._to_model_data(m) for m in model_all()]

    @inject
    def add(self, model: Model, modelset_add: ModelSetAddUc = Provide[UsecaseContainer.modelset_add_uc]) -> None:
        """
        Add a model to this model set.

        Adds the specified model to this model set and updates the model set's state.

        Parameters
        ----------
        model : Model
            The model to add to this model set.
        modelset_add : ModelSetAddUc, injected
            The use case for adding models to a model set, by default provided by dependency injection.
        """
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
        """
        Remove a model from this model set.

        Removes the specified model from this model set and updates the model set's state.

        Parameters
        ----------
        model : Model
            The model to remove from this model set.
        modelset_remove : ModelSetRemoveUc, injected
            The use case for removing models from a model set, by default provided by dependency injection.
        """
        result: Result[ModelSetDomain, Exception] = modelset_remove(dataset_id=self.id, model=model)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    @inject
    def delete(self, modelset_delete_uc: ModelSetDeleteUc = Provide[UsecaseContainer.modelset_delete_uc]) -> None:
        """
        Delete this model set from the database.

        Permanently removes this model set from the database.

        Parameters
        ----------
        modelset_delete_uc : ModelSetDeleteUc, injected
            The use case for deleting model sets, by default provided by dependency injection.
        """
        result: Result[None, Exception] = modelset_delete_uc(modelset_id=self.id)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

    def _update(self, modelset: ModelSetDomain) -> None:
        """
        Update this model set with data from a domain model.

        Updates the properties of this model set with values from the provided domain model.

        Parameters
        ----------
        modelset : ModelSetDomain
            The domain model containing the updated data.
        """
        self.id = modelset.id
        self.name = modelset.name
        self.models = [ModelSet._to_model_data(model=m) for m in modelset.models]

    @staticmethod
    def _to_model_data(model: ModelMetadataDomain) -> ModelData:
        """
        Convert a model metadata domain object to a ModelData object.

        Parameters
        ----------
        model : ModelMetadataDomain
            The model metadata domain object to convert.

        Returns
        -------
        ModelData
            The converted ModelData object.
        """
        return ModelData(id=model.id, model_name=model.name, model_hash=model.hash)

    @staticmethod
    def _to_data_set(dataset: ModelSetDomain) -> ModelSet:
        """
        Convert a model set domain object to a ModelSet object.

        Parameters
        ----------
        dataset : ModelSetDomain
            The model set domain object to convert.

        Returns
        -------
        ModelSet
            The converted ModelSet object.
        """
        return ModelSet(
            id=dataset.id,
            name=dataset.name,
            models=[ModelSet._to_model_data(m) for m in dataset.models],
        )
