from luna_bench.errors.validation_errors.validation_error import ValidationError


class ValidationSolutionError(ValidationError):
    """Base class for errors related to validating data."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"The solution field '{field_name}' must be a Solution or None.")
