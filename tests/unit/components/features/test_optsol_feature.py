from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from luna_bench.errors.infeasible_model_error import InfeasibleModelError

if TYPE_CHECKING:
    from luna_model import Model

from luna_bench.features.optsol_feature import OptSolFeature


class TestOptSolFeature:
    """Tests for the OptSolFeature class.

    The OptSolFeature class is used to determine the optimal solution for a given model. Users have the possibility
    to set time limits to avoid extensive executions. Additionally, it should be tested, how an infeasible model is
    handled and if the optimal solution for a simple model is found.
    """

    def test_time_limit_reached(self, hard_model: Model) -> None:
        """Test that the feature handles time limit correctly."""
        runtime_limit = 0.1
        # Set a short time limit to ensure pre-termination on complex problems
        feature = OptSolFeature(max_runtime=runtime_limit)
        result = feature.run(hard_model)

        # Should have pre-terminated due to time limit
        assert result.pre_terminated is True

        # Should still have a best solution (upper bound)
        assert isinstance(result.best_sol, float)

        # Runtime should be lower than defined limit
        assert result.runtime < (runtime_limit + 1)

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
