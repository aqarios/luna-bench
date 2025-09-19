from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging, Model
from returns.pipeline import is_successful

from luna_bench._internal.usecases import ModelAddUc, ModelLoadAllUc, ModelSetCreateUc
from luna_bench._internal.usecases.modelset.protocols import (
    ModelRemoveUc,
    ModelSetDeleteUc,
    ModelSetLoadAllUc,
    ModelSetLoadUc,
)
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench._internal.user_models import ModelSetUserModel
from luna_bench.components.model_metadata import ModelMetadata
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result


class ModelSet(ModelSetUserModel):
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
    models : list[ModelMetadata]
        A list of ModelData objects representing the models in this set.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    @staticmethod
    @inject
    def create(
        modelset_name: str, modelset_create: ModelSetCreateUc = Provide[UsecaseContainer.modelset_create_uc]
    ) -> ModelSet:
        """
        Create a new model set with the given dataset name.

        Creates a new model set using the provided dataset name and a model
        set creation use case.

        Parameters
        ----------
        modelset_name : str
            The name of the dataset.
        modelset_create : ModelSetCreateUc, injected
            The use case for creating model sets, by default, it's provided by dependency injection.

        Returns
        -------
        ModelSet
            An instance of ModelSet representing the successfully created model set.
        """
        result: Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError] = modelset_create(
            modelset_name=modelset_name
        )

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        return ModelSet.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    @inject
    def load(name: str, modelset_load: ModelSetLoadUc = Provide[UsecaseContainer.modelset_load_uc]) -> ModelSet:
        """
        Load a model set by its ID.

        Retrieves a model set from the database using its unique identifier.

        Parameters
        ----------
        name : str
            The unique name of the model set to load.
        modelset_load : ModelSetLoadUc, injected
            The use case for loading model sets, by default provided by dependency injection.

        Returns
        -------
        ModelSet
            The loaded model set.
        """
        result: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError] = modelset_load(modelset_name=name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        return ModelSet.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    @inject
    def load_all(
        modelset_load_all: ModelSetLoadAllUc = Provide[UsecaseContainer.modelset_load_all_uc],
    ) -> list[ModelSet]:
        """
        Load all model sets from the database.

        Retrieves all model sets stored in the database.

        Returns
        -------
        list[ModelSet]
            A list of all model sets.
        """
        result: Result[list[ModelSetUserModel], UnknownLunaBenchError] = modelset_load_all()

        if not is_successful(result):
            error = result.failure()
            raise RuntimeError(error)
        # TODO(Llewellyn): i think model validate for metadata is here missing # noqa: FIX002
        return [ModelSet.model_validate(m, from_attributes=True) for m in result.unwrap()]

    @staticmethod
    @inject
    def load_all_models(
        model_all: ModelLoadAllUc = Provide[UsecaseContainer.model_load_all_uc],
    ) -> list[ModelMetadata]:
        """
        Load all models from the database.

        Retrieves all models stored in the database, regardless of which model set they belong to.

        Parameters
        ----------
        model_all : ModelAllUc, injected
            The use case for retrieving all models, by default provided by dependency injection.

        Returns
        -------
        list[ModelMetadata]
            A list of ModelData objects representing all models in the database.
        """
        return [ModelMetadata.model_validate(m, from_attributes=True) for m in model_all()]

    @inject
    def add(self, model: Model, modelset_add: ModelAddUc = Provide[UsecaseContainer.model_add_uc]) -> None:
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
        result: Result[ModelSetUserModel, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError] = (
            modelset_add(modelset_name=self.name, model=model)
        )

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    @inject
    def remove_model(
        self, model: Model, modelset_remove: ModelRemoveUc = Provide[UsecaseContainer.model_remove_uc]
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
        result: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError] = modelset_remove(
            modelset_name=self.name, model=model
        )

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
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = modelset_delete_uc(modelset_name=self.name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

    def _update(self, modelset: ModelSetUserModel) -> None:
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
        self.models = [ModelMetadata.model_validate(m, from_attributes=True) for m in modelset.models]
