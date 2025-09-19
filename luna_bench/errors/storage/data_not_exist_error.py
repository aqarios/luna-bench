from luna_bench.errors.storage.dao_error import DaoError


class DataNotExistError(DaoError):
    """Raised when the requested data does not exist."""

    def __init__(self) -> None:
        super().__init__("The requested data does not exist.")
