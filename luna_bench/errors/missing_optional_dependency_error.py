from luna_bench.errors.base_error import BaseError


class MissingOptionalDependencyError(BaseError):
    """Raised when an optional dependency is required but not installed."""

    def __init__(self, package_name: str) -> None:
        """Initialize the error with a clear installation message.

        Args:
            package_name: Name of the missing package (e.g., 'matplotlib', 'scipy')
        """
        message = f"Install the 'pre-defined' extra to use {package_name}: luna-bench[pre-defined]"
        super().__init__(message)
