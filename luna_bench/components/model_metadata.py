from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from returns.pipeline import is_successful

from luna_bench._internal.usecases.modelset.protocols import ModelFetchUc
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench.entities.model_metadata_entity import ModelMetadataEntity
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_model import Model
    from returns.result import Result


class ModelMetadata(ModelMetadataEntity):
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

    @inject
    def _fetch_model(self, model_fetch: ModelFetchUc = Provide[UsecaseContainer.model_fetch_uc]) -> Model:
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
        result: Result[Model, DataNotExistError | UnknownLunaBenchError] = model_fetch(model_id=self.id)

        if not is_successful(result):
            error = result.failure()
            raise RuntimeError(error)

        return result.unwrap()

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
        return self._fetch_model()
