from luna_bench.errors.base_error import BaseError


class UnknownLunaBenchError(BaseError):
    """Raised when an unknown or unexpected error occurs."""

    exception: Exception

    def __init__(self, exception: Exception) -> None:
        super().__init__("An unknown error occurred.")
        self.exception = exception

    def error(self) -> Exception:
        """Get the exception which was wrapped."""
        return self.exception
