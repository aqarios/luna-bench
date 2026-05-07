from luna_bench.errors.base_error import BaseError


class InvalidWorkerTypeError(BaseError):
    """Raised when an invalid Huey worker type is specified."""

    def __init__(self, worker_type: str, valid_types: set[str]) -> None:
        self.worker_type = worker_type
        self.valid_types = valid_types
        msg = f"Invalid worker type: {worker_type}. Must be one of {valid_types}."
        super().__init__(msg)
