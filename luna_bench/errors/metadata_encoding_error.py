from luna_bench.errors.base_error import BaseError


class MetadataEncodingError(BaseError):
    """
    Raised when the metadata an algorithm returned cannot be serialized.

    Attributes
    ----------
    algorithm_name : str | None
        Name of the algorithm whose metadata could not be encoded, where it is known.
    error : Exception
        The exception the serializer raised.
    """

    algorithm_name: str | None
    error: Exception

    def __init__(self, error: Exception, algorithm_name: str | None = None) -> None:
        self.algorithm_name = algorithm_name
        self.error = error
        source = f"The metadata returned by '{algorithm_name}'" if algorithm_name else "The metadata of a run"
        super().__init__(
            f"{source} cannot be serialized: {error.__class__.__name__}: {error}. Metadata has to be "
            f"picklable, so report plain values instead of objects bound to an open connection, a file "
            f"handle or a lambda."
        )
