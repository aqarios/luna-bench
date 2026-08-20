from luna_bench.errors.dao.dao_error import DaoError


class DataNotExistError(DaoError):
    """Raised when the requested data does not exist."""

    def __init__(self, message: str | None = None) -> None:
        """Initialize the error.

        Parameters
        ----------
        message : str | None
            What was looked for and not found. Callers that know the answer
            should say so; the generic fallback names nothing at all.
        """
        super().__init__(message or "The requested data does not exist.")
