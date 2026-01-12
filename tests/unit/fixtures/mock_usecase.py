import pytest

from luna_bench import _usecase_container
from luna_bench._internal.usecases.usecase_container import UsecaseContainer

from .mock_database import SetupBenchmark


@pytest.fixture()
def usecase(setup_benchmark: SetupBenchmark) -> UsecaseContainer:  # noqa: ARG001 # here the setup_benchmark fixture is used, so that every test uses the a fresh new "db"
    """Provide a usecase fixture for testing usecases."""
    return _usecase_container
