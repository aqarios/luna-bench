from luna_bench.errors.registry.base_registry_error import BaseRegistryError


class AlreadyRegisteredIdError(BaseRegistryError):
    """Raised when an ID is already registered in a registry."""

    def __init__(self, registry: str, registered_id: str) -> None:
        self.component_name = registered_id
        super().__init__(f"The id '{registered_id}' is already registered in the '{registry}' registry.")
