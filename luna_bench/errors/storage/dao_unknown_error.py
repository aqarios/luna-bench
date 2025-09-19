from luna_bench.errors.storage.dao_error import DaoError


class DaoUnknownError(DaoError):
    """Raised when an unknown or unexpected error occurs."""

    exception: Exception

    def __init__(self, exception: Exception) -> None:
        super().__init__("An unknown database related error occurred.")
        self.exception = exception

    def error(self) -> Exception:
        """Get the exception which was wrapped."""
        return self.exception
