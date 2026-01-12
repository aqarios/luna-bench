from luna_bench.errors.base_error import BaseError


class IncompatibleClassError(BaseError):
    """Raised when a decorator is applied to an incompatible class."""

    def __init__(self, base_class: type | tuple[type, ...]) -> None:
        self.base_class = base_class
        if isinstance(base_class, tuple):
            names = ", ".join(getattr(t, "__name__", repr(t)) for t in base_class)
        else:
            names = getattr(base_class, "__name__", repr(base_class))
        super().__init__(f"Decorator can only be applied to subclasses of {names}.")
