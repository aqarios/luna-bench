from luna_bench.errors.dao.dao_error import DaoError


class DataNotUniqueError(DaoError):
    """Raised when the inserted/create data is not unique."""

    def __init__(self) -> None:
        super().__init__("The inserted/created data must not already exist.")
