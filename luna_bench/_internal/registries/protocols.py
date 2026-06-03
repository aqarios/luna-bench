from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from returns.result import Result

    from luna_bench.errors.registry.already_registerd_id_error import AlreadyRegisteredIdError
    from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class Registry[T](Protocol):
    """Protocol for a thread-safe, dictionary-backed registry mapping string IDs to classes."""

    def register(self, registered_id: str, cls: type[T]) -> Result[None, AlreadyRegisteredIdError]:
        """
        Register a class under a given ID.

        Parameters
        ----------
        registered_id: str
            The ID to register the class under.
        cls: type[T]
            The class to register.

        Returns
        -------
        Result[None, AlreadyRegisteredIdError]
            On success: ``Success(None)``.
            On failure: ``Failure(AlreadyRegisteredIdError)`` if the ID is already taken.
        """

    def get_by_id(self, registered_id: str) -> Result[type[T], UnknownIdError]:
        """
        Retrieve a registered class by its ID.

        Parameters
        ----------
        registered_id: str
            The ID of the registered class.

        Returns
        -------
        Result[type[T], UnknownIdError]
            On success: ``Success(cls)`` with the class associated with the given ID.
            On failure: ``Failure(UnknownIdError)`` if the ID was not found.
        """

    def get_by_cls(self, cls: type[T]) -> Result[str, UnknownComponentError]:
        """
        Retrieve the ID for a registered class via identity comparison.

        Parameters
        ----------
        cls: type[T]
            The exact registered class instance to look up.

        Returns
        -------
        Result[str, UnknownComponentError]
            On success: ``Success(id)`` with the ID associated with the given class.
            On failure: ``Failure(UnknownComponentError)`` if the class was not found.
        """

    def ids(self) -> list[str]:
        """
        Return a snapshot list of all registered IDs.

        Returns
        -------
        list[str]
            A list of all currently registered IDs.
        """

    def classes(self) -> Mapping[str, type[T]]:
        """
        Return a snapshot mapping of all registered IDs to their classes.

        Returns
        -------
        Mapping[str, type[T]]
            A dictionary mapping each registered ID to its corresponding class.
        """

    def contains(self, registered_id: str) -> bool:
        """
        Check whether an ID is currently registered.

        Parameters
        ----------
        registered_id: str
            The ID to check.

        Returns
        -------
        bool
            ``True`` if the ID is registered, ``False`` otherwise.
        """


class PydanticRegistry[USER_MODEL: BaseModel, DOMAIN_MODEL: BaseModel](Registry[USER_MODEL], Protocol):
    """Protocol for a registry with bidirectional conversion between user-facing and domain Pydantic models."""

    def from_domain_to_user_model(
        self, domain_model: DOMAIN_MODEL
    ) -> Result[USER_MODEL, UnknownIdError | ValidationError]:
        """
        Deserialize a domain model into the corresponding user-facing model.

        Parameters
        ----------
        domain_model: DOMAIN_MODEL
            The domain (serialized) model to convert.

        Returns
        -------
        Result[USER_MODEL, UnknownIdError | ValidationError]
            On success: ``Success(user_model)`` with the reconstructed user model.
            On failure: ``Failure(UnknownIdError)`` if the registered ID is unknown,
            or ``Failure(ValidationError)`` if the payload data is invalid.
        """

    def from_user_model_to_domain_model(self, user_model: USER_MODEL) -> Result[DOMAIN_MODEL, UnknownComponentError]:
        """
        Serialize a user-facing model into the corresponding domain model.

        Parameters
        ----------
        user_model: USER_MODEL
            The user-facing model to serialize.

        Returns
        -------
        Result[DOMAIN_MODEL, UnknownComponentError]
            On success: ``Success(domain_model)`` with the serialized domain model.
            On failure: ``Failure(UnknownComponentError)`` if the class is not registered.
        """
