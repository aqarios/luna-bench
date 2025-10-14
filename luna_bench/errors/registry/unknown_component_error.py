from luna_bench.errors.registry.base_registry_error import BaseRegistryError


class UnknownComponentError(BaseRegistryError):
    """Raised when a component is not known to a registry."""

    def __init__(self, registry: str, cls: type) -> None:
        self.registry = registry
        self.unknown_cls = cls
        super().__init__(f"The class '{id}' is unknown in the '{registry}' registry.")
