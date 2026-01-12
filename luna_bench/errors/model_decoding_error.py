from luna_bench.errors.base_error import BaseError


class ModelDecodingError(BaseError):
    """Raised when an unknown or unexpected error occurs."""

    model_bytes: bytes
    exception: Exception

    def __init__(self, model_bytes: bytes, exception: Exception) -> None:
        self.model_bytes = model_bytes
        self.exception = exception

        super().__init__(f"Failed to convert the bytes into an Model obj: '{model_bytes!r}'.")

    def error(self) -> Exception:
        """Get the exception which was wrapped."""
        return self.exception
