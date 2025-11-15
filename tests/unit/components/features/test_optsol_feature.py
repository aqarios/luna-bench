from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from luna_quantum import Model

from luna_bench.components.features.optsol_feature import InfeasibleModelError, OptSolFeature


class TestOptSolFeature:
    """Tests for the OptSolFeature class."""

    def test_time_limit_reached(self, hard_model: Model) -> None:
        """Test that the feature handles time limit correctly."""
        # Set a short time limit to ensure pre-termination on complex problems
        feature = OptSolFeature(max_runtime=1)
        result = feature.run(hard_model)

        # Should have pre-terminated due to time limit
        assert result.pre_terminated is True

        # Should still have a best solution (upper bound)
        assert isinstance(result.best_sol, float)

    def test_infeasible_model(self, infeasible_model: Model) -> None:
        """Test that the feature raises InfeasibleModelError for infeasible models."""
        feature = OptSolFeature()

        with pytest.raises(InfeasibleModelError):
            feature.run(infeasible_model)

    def test_regular_model(self, regular_model: Model) -> None:
        """Test that the feature returns correct result for a solvable model."""
        feature = OptSolFeature()
        result = feature.run(regular_model)

        # Should not have pre-terminated
        assert result.pre_terminated is False
        # Should have a best solution as a float
        assert isinstance(result.best_sol, float)
        # For this specific model, the optimal solution should be 0 (minimize x + y with x, y >= 0)
        assert result.best_sol == 0.0
