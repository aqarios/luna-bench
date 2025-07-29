from luna_bench.errors.base_error import BaseError


class DataNotExistError(BaseError):
    """Raised when the requested data does not exist."""

    def __init__(self) -> None:
        super().__init__("The requested data does not exist.")
