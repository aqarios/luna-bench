from collections.abc import Mapping
from logging import Logger
from threading import RLock

from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench._internal.registries.protocols import Registry
from luna_bench.errors.registry.already_registerd_id_error import AlreadyRegisteredIdError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class BaseRegistry[T](Registry[T]):
    _kind: str
    _by_id: dict[str, type[T]]
    _lock: RLock

    _logging: Logger = Logging.get_logger(__name__)

    def __init__(self, kind: str) -> None:
        self._kind: str = kind
        self._by_id: dict[str, type[T]] = {}
        self._lock: RLock = RLock()

    def register(self, registered_id: str, cls: type[T]) -> Result[None, AlreadyRegisteredIdError]:
        """
        Register a plugin class with a unique registered_id and optional aliases.

        Raises
        ------
        AlreadyRegisteredIdError
            If registered_id is already registered or an alias collides.
        """
        with self._lock:
            if registered_id in self._by_id:
                existing: type[T] = self._by_id[registered_id]
                self._logging.warning(f"{self._kind} '{registered_id}' already registered by {existing!r}")
                return Failure(AlreadyRegisteredIdError(self._kind, registered_id))
            self._by_id[registered_id] = cls
            return Success(None)

    def get_by_id(self, registered_id: str) -> Result[type[T], UnknownIdError]:
        """
        Resolve a class by registered_id or alias.

        Raises
        ------
        UnknownIdError
            If no plugin matches.
        """
        with self._lock:
            try:
                return Success(self._by_id[registered_id])
            except KeyError:
                self._logging.warning(f"Unknown {self._kind} '{registered_id}'")
                return Failure(UnknownIdError(self._kind, registered_id))

    def get_by_cls(self, cls: type[T]) -> Result[str, UnknownComponentError]:
        """
        Resolve a class by registered_id or alias.

        Raises
        ------
        UnknownComponentError
            If no plugin matches.
        """
        with self._lock:
            for k, v in self._by_id.items():
                if v is cls:
                    return Success(k)
            return Failure(UnknownComponentError(self._kind, cls))

    def ids(self) -> list[str]:
        """Return all registered plugin IDs."""
        with self._lock:
            return list(self._by_id.keys())

    def classes(self) -> Mapping[str, type[T]]:
        """Return a read-only copy of registered_id -> class mapping."""
        with self._lock:
            return dict(self._by_id)

    def contains(self, registered_id: str) -> bool:
        """Check if a registered id is known."""
        with self._lock:
            return registered_id in self._by_id
