from luna_bench.errors.missing_optional_dependency_error import (
    MissingOptionalDependencyError,
)


def check_optional_dependency(package_name: str) -> None:
    """Check if an optional dependency is installed.

    Args:
        package_name: Name of the package to check (e.g., 'matplotlib', 'scipy')

    Raises
    ------
        MissingOptionalDependencyError: If the package is not installed.
    """
    try:
        __import__(package_name)
    except ImportError as e:
        raise MissingOptionalDependencyError(package_name) from e
