from luna_bench.errors.base_error import BaseError


class ModelNameAlreadyUsedError(BaseError):
    """Raised when trying to add a model with a name that is already used by another model."""

    def __init__(self, model_name: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        model_name : str
            The name that is already taken by a different model.
        """
        self.model_name = model_name
        super().__init__(
            f"A different model with the name '{model_name}' already exists. Model names are "
            f"unique across the whole database, not per modelset, so this clashes even if the "
            f"other model lives in a modelset you are not using. Rename this model - for models "
            f"read from a file, that means renaming the file, since the file stem becomes the name."
        )
