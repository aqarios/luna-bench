from luna_bench.errors.base_error import BaseError


class MetadataDecodingError(BaseError):
    """
    Raised when stored metadata cannot be deserialized again.

    Attributes
    ----------
    error : Exception
        The exception the deserializer raised.
    """

    error: Exception

    def __init__(self, error: Exception) -> None:
        self.error = error
        super().__init__(
            f"The stored metadata of an algorithm result cannot be deserialized: {error.__class__.__name__}: {error}."
        )
