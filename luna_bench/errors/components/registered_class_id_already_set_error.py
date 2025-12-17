from luna_bench.errors.components.component_error import ComponentError


class RegisteredClassIdAlreadySetError(ComponentError):
    """Error raised when the registered_id of a registered class is already set."""

    def __init__(self, registered_id: str) -> None:
        self.registered_id = registered_id
