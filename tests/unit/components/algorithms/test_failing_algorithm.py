import pytest
from luna_quantum import Model

from tests.fixtures.failing_algorithm import (
    FailingAlgorithm,
    FailingArbitraryErrorAlgorithm,
    _CustomError,
)


class TestFailingAlgorithm:
    """Tests for the FailingAlgorithm class."""

    def test_failing_algorithm(self, empty_model: Model) -> None:
        """Test that the FailingAlgorithm raises an error."""
        with pytest.raises(_CustomError):
            FailingAlgorithm().run(empty_model)


class TestFailingArbitraryAlgorithm:
    """Tests for the the FailingAlgorithm class."""

    def test_failing_algorithm(self, empty_model: Model) -> None:
        """Test that the FailingAlgorithm raises an error."""
        with pytest.raises(ValueError, match=r"This algorithm failed due to an ValueError error."):
            FailingArbitraryErrorAlgorithm().run(empty_model)
