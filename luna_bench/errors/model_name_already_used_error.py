from luna_bench.errors.base_error import BaseError


class ModelNameAlreadyUsedError(BaseError):
    """Raised when trying to add a model with a name that is already used by another model."""

    def __init__(self, model_name: str) -> None:
        super().__init__(f"A different model with the name '{model_name}' already exists.")
