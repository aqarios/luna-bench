"""Tests for the FeasibilityRatio metric."""

from __future__ import annotations

import time

from luna_quantum import Sense, Solution, Timer, Vtype

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult


def _create_solution(
    obj_values: list[float],
    feasible: list[bool],
    sense: Sense = Sense.Min,
    runtime_seconds: float = 0.01,
) -> Solution:
    """Create a Solution with specific objective values and feasibility."""
    timer = Timer.start()
    time.sleep(runtime_seconds)
    timing = timer.stop()

    num_samples = len(obj_values)
    return Solution._build(  # type: ignore[attr-defined,no-any-return]
        component_types=[Vtype.Binary],
        binary_cols=[[0] * num_samples],
        raw_energies=obj_values,
        timing=timing,
        counts=[1] * num_samples,
        sense=sense,
        obj_values=obj_values,
        feasible=feasible,
    )


def _create_empty_feature_results() -> FeatureResults:
    """Create empty FeatureResults (FeasibilityRatio doesn't need features)."""
    return FeatureResults(allowed=[], data={})


class TestFeasibilityRatioResult:
    """Tests for FeasibilityRatioResult."""

    def test_valid_result_all_feasible(self) -> None:
        """Test that a feasibility ratio of 1.0 (all feasible) is valid."""
        result = FeasibilityRatioResult(feasibility_ratio=1.0)
        assert result.feasibility_ratio == 1.0

    def test_valid_result_none_feasible(self) -> None:
        """Test that a feasibility ratio of 0.0 (none feasible) is valid."""
        result = FeasibilityRatioResult(feasibility_ratio=0.0)
        assert result.feasibility_ratio == 0.0

    def test_valid_result_partial(self) -> None:
        """Test that a feasibility ratio between 0 and 1 is valid."""
        result = FeasibilityRatioResult(feasibility_ratio=0.5)
        assert result.feasibility_ratio == 0.5


class TestFeasibilityRatio:
    """Tests for the FeasibilityRatio metric."""

    def test_all_feasible(self) -> None:
        """Test feasibility ratio = 1.0 when all solutions are feasible."""
        solution = _create_solution(
            obj_values=[10.0, 20.0, 30.0],
            feasible=[True, True, True],
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 1.0

    def test_none_feasible(self) -> None:
        """Test feasibility ratio = 0.0 when no solutions are feasible."""
        solution = _create_solution(
            obj_values=[10.0, 20.0, 30.0],
            feasible=[False, False, False],
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 0.0

    def test_partial_feasibility(self) -> None:
        """Test feasibility ratio when some solutions are feasible."""
        solution = _create_solution(
            obj_values=[10.0, 20.0, 30.0, 40.0],
            feasible=[True, False, True, False],
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 0.5  # 2 out of 4

    def test_one_third_feasible(self) -> None:
        """Test feasibility ratio with 1/3 feasible solutions."""
        solution = _create_solution(
            obj_values=[10.0, 20.0, 30.0],
            feasible=[True, False, False],
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert abs(result.feasibility_ratio - 1 / 3) < 0.001

    def test_empty_solution(self) -> None:
        """Test that empty solution returns 0.0."""
        timer = Timer.start()
        time.sleep(0.01)
        timing = timer.stop()

        solution = Solution._build(  # type: ignore[attr-defined]
            component_types=[Vtype.Binary],
            binary_cols=[[]],
            timing=timing,
            sense=Sense.Min,
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 0.0

    def test_single_feasible_sample(self) -> None:
        """Test feasibility ratio with a single feasible sample."""
        solution = _create_solution(
            obj_values=[10.0],
            feasible=[True],
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 1.0

    def test_single_infeasible_sample(self) -> None:
        """Test feasibility ratio with a single infeasible sample."""
        solution = _create_solution(
            obj_values=[10.0],
            feasible=[False],
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 0.0

    def test_maximization_problem(self) -> None:
        """Test that feasibility ratio works for maximization problems too."""
        solution = _create_solution(
            obj_values=[10.0, 20.0],
            feasible=[True, False],
            sense=Sense.Max,
        )
        feature_results = _create_empty_feature_results()

        metric = FeasibilityRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 0.5
