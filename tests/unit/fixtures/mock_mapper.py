import pytest

from luna_bench import MapperContainer, _mapper_container  # type: ignore[attr-defined]


@pytest.fixture()
def mapper() -> MapperContainer:
    """Provide a usecase fixture for testing usecases."""
    return _mapper_container
