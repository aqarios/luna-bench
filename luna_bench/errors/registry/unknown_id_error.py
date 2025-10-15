from luna_bench.errors.registry.base_registry_error import BaseRegistryError


class UnknownIdError(BaseRegistryError):
    """Raised when an ID is not known to a registry."""

    def __init__(self, registry: str, registered_id: str) -> None:
        self.registry = registry
        self.unknown_id = registered_id
        super().__init__(f"The id '{registered_id}' is unknown in the '{registry}' registry.")
