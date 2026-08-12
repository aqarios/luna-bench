from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from luna_model import Sense
from pydantic import ValidationError

from luna_bench.errors.infeasible_model_error import InfeasibleModelError
from tests.utils.luna_model import simple_model

if TYPE_CHECKING:
    from luna_model import Model

    from tests.unit.fixtures.mock_feature_results import SolutionFactory

from luna_bench.features.optsol_feature import OptSolFeature, OptSolFeatureResult


@pytest.fixture()
def model_a() -> Model:
    return simple_model("model_a")


@pytest.fixture()
def model_b() -> Model:
    return simple_model("model_b")


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
        assert isinstance(result.global_best_sol, float)

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
        assert isinstance(result.global_best_sol, float)

        # For this specific model, the optimal solution should be 0 (minimize x + y with x, y >= 0)
        assert result.global_best_sol == 0.0


class TestOptSolFeatureResult:
    """Tests for the result, which is also what a known optimum is registered as."""

    def test_defaults_to_a_proven_optimum(self) -> None:
        """Test that a registered value is a proven optimum unless said otherwise."""
        assert OptSolFeatureResult(global_best_sol=42.0).pre_terminated is False

    def test_defaults_to_no_runtime(self) -> None:
        """Test that a registered value needs no runtime, since it was not solved for."""
        assert OptSolFeatureResult(global_best_sol=42.0).runtime == 0.0

    def test_records_an_unproven_bound(self) -> None:
        """Test that a best-known but unproven value can be marked as such."""
        assert OptSolFeatureResult(global_best_sol=42.0, pre_terminated=True).pre_terminated is True

    def test_rejects_a_non_numeric_objective(self) -> None:
        """Test that a bad objective is caught at registration rather than at use."""
        with pytest.raises(ValidationError):
            OptSolFeatureResult(global_best_sol="not a number")  # type: ignore[arg-type]

    def test_from_solution_takes_the_best_objective(self, create_solution: SolutionFactory) -> None:
        """Test that a record built from a solution carries its best sample's objective."""
        solution = create_solution(obj_values=[3.0, 1.0, 2.0], sense=Sense.MIN, feasible=[True, True, True])

        record = OptSolFeatureResult.from_solution(solution, pre_terminated=False)

        assert record.global_best_sol == pytest.approx(1.0)
        assert record.pre_terminated is False
        assert record.runtime == 0.0

    def test_from_solution_keeps_the_pre_terminated_flag(self, create_solution: SolutionFactory) -> None:
        """Test that from_solution passes the caller's proven/unproven judgement through."""
        solution = create_solution(obj_values=[1.0], feasible=[True])

        assert OptSolFeatureResult.from_solution(solution, pre_terminated=True).pre_terminated is True

    def test_from_solution_rejects_a_solution_without_feasible_samples(self, create_solution: SolutionFactory) -> None:
        """Test that a solution with nothing feasible cannot become a record."""
        solution = create_solution(obj_values=[1.0], feasible=[False])

        with pytest.raises(ValueError, match="no feasible sample"):
            OptSolFeatureResult.from_solution(solution, pre_terminated=False)


class TestOptSolFeaturePreComputed:
    """A registered model is served from the mapping instead of being solved."""

    def test_serves_the_registered_objective(self, model_a: Model) -> None:
        """Test that a registered value comes back as the feature result."""
        feature = OptSolFeature()
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=42.0))

        result = feature.run(model_a)

        assert isinstance(result, OptSolFeatureResult)
        assert result.global_best_sol == 42.0
        assert result.pre_terminated is False
        assert result.runtime == 0.0

    def test_the_result_does_not_alias_the_mapping(self, model_a: Model) -> None:
        """Test that mutating a returned result cannot change what the next run sees."""
        feature = OptSolFeature()
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=42.0))

        feature.run(model_a).global_best_sol = 99.0

        assert feature.run(model_a).global_best_sol == 42.0

    def test_passes_the_pre_terminated_flag_through(self, model_a: Model) -> None:
        """Test that an unproven bound is reported as pre-terminated."""
        feature = OptSolFeature()
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=42.0, pre_terminated=True))

        assert feature.run(model_a).pre_terminated is True

    def test_does_not_solve(self, model_a: Model) -> None:
        """Test that a registered model skips the solver, which is the point of registering it."""
        feature = OptSolFeature()
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=42.0))

        with patch.object(OptSolFeature, "on_miss") as on_miss:
            feature.run(model_a)

        on_miss.assert_not_called()

    def test_add_models_registers_a_collection(self, model_a: Model, model_b: Model) -> None:
        """Test that a whole collection of known optima can be registered at once."""
        feature = OptSolFeature()
        feature.add_models(
            {model_a: OptSolFeatureResult(global_best_sol=1.0), model_b: OptSolFeatureResult(global_best_sol=2.0)}
        )

        assert feature.run(model_a).global_best_sol == 1.0
        assert feature.run(model_b).global_best_sol == 2.0

    def test_covers_reports_the_gaps_up_front(self, model_a: Model, model_b: Model) -> None:
        """Test that a modelset can be checked for gaps without running the feature."""
        feature = OptSolFeature()
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=1.0))

        assert feature.covers(model_a) is True
        assert feature.covers(model_b) is False

    def test_an_unregistered_model_is_still_solved(self, model_a: Model, model_b: Model) -> None:
        """Test that registering one model does not stop another from being solved."""
        feature = OptSolFeature()
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=42.0))

        with patch.object(OptSolFeature, "on_miss") as on_miss:
            on_miss.return_value = OptSolFeatureResult(global_best_sol=7.0, pre_terminated=False, runtime=0.5)
            assert feature.run(model_a).global_best_sol == 42.0
            assert feature.run(model_b).global_best_sol == 7.0

        on_miss.assert_called_once_with(model_b)

    def test_an_unpopulated_feature_solves_every_model(self, regular_model: Model) -> None:
        """Test that the feature behaves exactly as before when nothing is registered."""
        feature = OptSolFeature()

        assert feature.covers(regular_model) is False
        assert feature.run(regular_model).global_best_sol == 0.0

    def test_round_trips_through_json(self, model_a: Model) -> None:
        """Test that a populated feature reconstructs from its own JSON, as the benchmark stores it."""
        feature = OptSolFeature(max_runtime=60.0)
        feature.add_model(model_a, OptSolFeatureResult(global_best_sol=42.0, pre_terminated=True))

        restored = OptSolFeature.model_validate_json(feature.model_dump_json())

        assert restored.mapping == feature.mapping
        assert restored.max_runtime == 60.0
        assert restored.run(model_a).global_best_sol == 42.0
        assert restored.run(model_a).pre_terminated is True
