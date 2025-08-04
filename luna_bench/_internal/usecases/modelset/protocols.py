from typing import Protocol

from luna_quantum import Model
from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelSetDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelSetCreateUc(Protocol):
    """Protocol for creating a new model set."""

    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]:
        """
        Create a new model set with the given name.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to create.

        Returns
        -------
        Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]
            On success: Contains the created model set object
            On failure: An Exception
        """


class ModelSetLoadUc(Protocol):
    """Protocol for loading a model set."""

    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        """
        Load a specific model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to load.

        Returns
        -------
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the model set object
            On failure: An Exception
        """


class ModelSetAddUc(Protocol):
    """Protocol for adding a model to a model set."""

    def __call__(
        self, modelset_name: str, model: Model
    ) -> Result[ModelSetDomain, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError]:
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
        Result[ModelSetDomain, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError]
            On success: Contains the updated model set object
            On failure: An Exception
        """


class ModelSetListUc(Protocol):
    """Protocol for listing all model sets."""

    def __call__(self) -> Result[list[ModelSetDomain], UnknownLunaBenchError]:
        """
        List all model sets.

        Returns
        -------
        Result[list[ModelSetDomain], UnknownLunaBenchError]
            On success: Contains a list of all model sets in storage.
            On failure: An Exception
        """


class ModelSetRemoveUc(Protocol):
    """Protocol for removing a model from a model set."""

    def __call__(
        self, modelset_name: str, model: Model
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
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
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the updated model set object
            On failure: An Exception
        """


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


class ModelSetLoadAllUc(Protocol):
    """Protocol for loading all model sets."""

    def __call__(self) -> Result[list[ModelSetDomain], UnknownLunaBenchError]:
        """
        Load all model sets.

        Returns
        -------
        Result[list[ModelSetDomain], UnknownLunaBenchError]
            On success: Contains the list of all model sets
            On failure: An Exception
        """
