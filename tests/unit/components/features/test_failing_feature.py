import pytest
from luna_quantum import Model

from tests.fixtures.failing_feature import FailingFeature


class TestFailingFeature:
    """Tests for the FailingFeature."""

    def test_range_fake(self, empty_model: Model) -> None:
        """Test that FailingFeature.run raises ValueError."""
        f_feature = FailingFeature()
        with pytest.raises(ValueError, match="Failing Feature because of Value Error"):
            f_feature.run(empty_model)
