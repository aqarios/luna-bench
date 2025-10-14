from typing import Protocol

from luna_quantum import Model
from returns.result import Result

from luna_bench._internal.user_models import ModelMetadataUserModel, ModelSetUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelLoadAllUc(Protocol):
    """Protocol for retrieving all models."""

    def __call__(self) -> list[ModelMetadataUserModel]:
        """
        Retrieve all models from dao.

        Returns
        -------
        list[ModelMetadataUserModel]
            A list of all model metadata domain objects.
        """
        ...


class ModelFetchUc(Protocol):
    """Protocol for retrieving model data from the database."""

    def __call__(self, model_id: int) -> Result[Model, DataNotExistError | UnknownLunaBenchError]:
        """
        Retrieve model data from the database.

        Parameters
        ----------
        model_id : int
            The id of the model to fetch.

        Returns
        -------
        Result[Model, DataNotExistError | UnknownLunaBenchError]
            On Success: The model data fetched from the database.
            On Failure: An error.
        """
        ...


class ModelSetCreateUc(Protocol):
    """Protocol for creating a new model set."""

    def __call__(self, modelset_name: str) -> Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError]:
        """
        Create a new model set with the given name.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to create.

        Returns
        -------
        Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError]
            On success: Contains the created model set object
            On failure: An Exception
        """
        ...


class ModelSetLoadUc(Protocol):
    """Protocol for loading a model set."""

    def __call__(self, modelset_name: str) -> Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError]:
        """
        Load a specific model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to load.

        Returns
        -------
        Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the model set object
            On failure: An Exception
        """
        ...


class ModelAddUc(Protocol):
    """Protocol for adding a model to a model set."""

    def __call__(
        self, modelset_name: str, model: Model
    ) -> Result[ModelSetUserModel, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError]:
        """
        Add a model to the model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to add the model to.
        model : Model
            The model to add to the model set.

        Returns
        -------
        Result[ModelSetUserModel, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError]
            On success: Contains the updated model set object
            On failure: An Exception
        """
        ...


class ModelRemoveUc(Protocol):
    """Protocol for removing a model from a model set."""

    def __call__(
        self, modelset_name: str, model: Model
    ) -> Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError]:
        """
        Remove a model from the model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to remove the model from.
        model : Model
            The model to remove from the model set.

        Returns
        -------
        Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the updated model set object
            On failure: An Exception
        """
        ...


class ModelSetDeleteUc(Protocol):
    """Protocol for deleting a model set."""

    def __call__(self, modelset_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """
        Delete a model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing
            On failure: An Exception
        """
        ...


class ModelSetLoadAllUc(Protocol):
    """Protocol for loading all model sets."""

    def __call__(self) -> Result[list[ModelSetUserModel], UnknownLunaBenchError]:
        """
        Load all model sets.

        Returns
        -------
        Result[list[ModelSetUserModel], UnknownLunaBenchError]
            On success: Contains the list of all model sets
            On failure: An Exception
        """
        ...
