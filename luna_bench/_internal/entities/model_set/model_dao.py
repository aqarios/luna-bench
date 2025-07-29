from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .domain_models import ModelMetadataDomain
from .tables import ModelMetadataTable, ModelTable

if TYPE_CHECKING:
    from logging import Logger


class ModelDAO:
    """
    Data Access Object for model operations.

    Provides methods for creating, retrieving, and managing model data in the database.
    Handles the conversion between database table objects and domain model objects.
    """

    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError]:
        """
        Retrieve a model by its hash value.

        Attempts to fetch a model from the database using its hash value.

        Parameters
        ----------
        model_hash : int
            The hash value of the model to retrieve.

        Returns
        -------
        Result[ModelMetadataDomain, DataNotExistError]
            On success: Contains the model metadata object
            On failure: Contains a DataNotExistError.
        """
        try:
            model = ModelMetadataTable.get(ModelMetadataTable.hash == model_hash)
            return Success(ModelDAO.model_to_domain(model))
        except ModelMetadataTable.DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]:
        """Retrieve the metadata of all models from the database.

        Returns
        -------
        list[ModelMetadataDomain]
            A metadata list of all model objects in the database.
        """
        data = ModelMetadataTable.select()
        return [ModelDAO.model_to_domain(d) for d in data]

    @staticmethod
    def get_or_create(model_name: str, model_hash: int, binary: bytes) -> Result[ModelMetadataDomain, Exception]:
        """Get an existing model or create a new one.

        Attempts to retrieve a model with the specified hash. If not found, creates a new model
        with the provided name, hash, and binary data.

        Parameters
        ----------
        model_name : str
            The name of the model.
        model_hash : int
            The hash value of the model.
        binary : bytes
            The binary data of the model.

        Returns
        -------
        Result[ModelMetadataDomain, Exception]
            On success: Contains the model metadata object, newly created or loaded.
            On failure: Contains an exception.
        """
        try:
            metadata, created = ModelMetadataTable.get_or_create(hash=model_hash, defaults={"name": model_name})

            if created:
                ModelTable.create(model_id=metadata, encoded_model=binary)

            return Success(ModelDAO.model_to_domain(metadata))
        except Exception as e:
            ModelDAO._logger.debug(e)
            return Failure(e)

    @staticmethod
    def fetch_model(model_id: int) -> Result[bytes, DataNotExistError]:
        """
        Fetch the binary data of a model.

        Retrieves the encoded binary data of a model from the database using its ID.

        Parameters
        ----------
        model_id : int
            The ID of the model to fetch.

        Returns
        -------
        Result[bytes, DataNotExistError]
            On success: Contains the encoded model binary data.
            On failure: Contains an exception.
        """
        try:
            data = ModelTable.get(ModelTable.model_id == model_id)

            return Success(data.encoded_model)
        except Exception as e:
            ModelDAO._logger.debug(e)
            return Failure(DataNotExistError())

    @staticmethod
    def model_to_domain(model: ModelMetadataTable) -> ModelMetadataDomain:
        """
        Convert a model table object to a domain model.

        Transforms a database model object into a domain model object.

        Parameters
        ----------
        model : ModelMetadataTable
            The database model object to convert.

        Returns
        -------
        ModelMetadataDomain
            The converted domain model object.
        """
        return ModelMetadataDomain(id=cast("int", model.id), name=cast("str", model.name), hash=cast("int", model.hash))
