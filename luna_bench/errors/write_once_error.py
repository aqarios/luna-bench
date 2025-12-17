from luna_bench.errors.base_error import BaseError


class WriteOnceError(BaseError):
    """Raised when an field is changed, which is suposed to be only changed once."""

    def __init__(self, class_name: str, field_name: str) -> None:
        super().__init__(f"The field '{field_name}' for the class '{class_name}' should only be changed/written once.")
