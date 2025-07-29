from luna_bench.errors.base_error import BaseError


class DataNotUniqueError(BaseError):
    """Raised when the inserted/create data is not unique."""

    def __init__(self) -> None:
        super().__init__("The inserted/created data must not already exist.")
