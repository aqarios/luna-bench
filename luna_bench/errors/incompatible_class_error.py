from luna_bench.errors.base_error import BaseError


class IncompatibleClassError(BaseError):
    """Raised when a decorator is applied to an incompatible class."""

    def __init__(self, base_class: type) -> None:
        self.base_class = base_class
        super().__init__(f"Decorator can only be applied to subclasses of {base_class.__name__}.")
