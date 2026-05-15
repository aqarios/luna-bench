"""Tests for the TimeToSolution metric."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np
import pytest
from luna_model import Sense, Solution, Timer, Vtype
from pydantic import ValidationError

from luna_bench.metrics.time_to_solution import TimeToSolution, TimeToSolutionResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from tests.unit.fixtures.mock_feature_results import SolutionFactory


class TestTimeToSolutionResult:
    """Tests for TimeToSolutionResult."""

    def test_valid_result(self) -> None:
        """Test that TimeToSolutionResult stores values correctly."""
        result = TimeToSolutionResult(
            time_to_solution=1.5,
            probability_optimal=0.5,
            num_optimal_found=5,
            num_samples=10,
        )
        assert result.time_to_solution == 1.5
        assert result.probability_optimal == 0.5
        assert result.num_optimal_found == 5
        assert result.num_samples == 10

    @pytest.mark.parametrize(
        ("tts", "prob", "found", "samples"),
        [
            (-1.0, 0.5, 5, 10),  # negative TTS
            (1.0, -0.1, 5, 10),  # probability < 0
            (1.0, 1.1, 5, 10),  # probability > 1
            (1.0, 0.5, -1, 10),  # negative num_optimal_found
            (1.0, 0.5, 5, -1),  # negative num_samples
        ],
    )
    def test_invalid_result(self, tts: float, prob: float, found: int, samples: int) -> None:
        """Test that infeasible results raise a ValidationError."""
        with pytest.raises(ValidationError):
            TimeToSolutionResult(
                time_to_solution=tts,
                probability_optimal=prob,
                num_optimal_found=found,
                num_samples=samples,
            )


class TestTimeToSolution:
    """Tests for the TimeToSolution metric."""

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_all_optimal_solutions(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS when all samples are optimal (p* = 1)."""
        solution = create_solution(obj_values=[5.0, 5.0, 5.0], sense=Sense.MIN, runtime_seconds=0.1)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 1.0
        assert result.num_optimal_found == 3
        assert result.num_samples == 3
        # When p* = 1, TTS = t_per_sample = total_time / num_samples
        assert result.time_to_solution == pytest.approx(solution.runtime.total_seconds / 3, abs=1e-6)  # type: ignore[union-attr]

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_no_optimal_solutions(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS = infinity when no optimal solutions found (p* = 0)."""
        solution = create_solution(obj_values=[10.0, 15.0, 20.0], sense=Sense.MIN)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 0.0
        assert result.num_optimal_found == 0
        assert result.num_samples == 3
        assert result.time_to_solution == float("inf")

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_some_optimal_solutions(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS calculation when some samples are optimal (0 < p* < 1)."""
        # 2 out of 4 samples are optimal
        solution = create_solution(obj_values=[5.0, 10.0, 5.0, 15.0], sense=Sense.MIN, runtime_seconds=0.1)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 0.5
        assert result.num_optimal_found == 2
        assert result.num_samples == 4

        # TTS formula: (t/M) * ceil(log(1-0.99) / log(1-p*))
        # With p* = 0.5: ceil(log(0.01) / log(0.5)) = ceil(6.64) = 7
        if solution.runtime is not None:
            total_runtime = solution.runtime.total_seconds
            t_per_sample = total_runtime / 4
            expected_tts = t_per_sample * np.ceil(np.log(0.01) / np.log(0.5))
            assert np.isclose(result.time_to_solution, expected_tts, rtol=0.01)

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_empty_solution(self, mock_feature_results: MagicMock) -> None:
        """Test that empty solution returns infinity."""
        timer = Timer.start()
        time.sleep(0.01)
        timing = timer.stop()

        solution = Solution(
            [],
            vtypes=[Vtype.BINARY],
            timing=timing,
            sense=Sense.MIN,
        )

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.time_to_solution == float("inf")
        assert result.probability_optimal == 0.0
        assert result.num_optimal_found == 0
        assert result.num_samples == 0

    @pytest.mark.parametrize("mock_feature_results", [20.0], indirect=True)
    def test_maximization_problem(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS for maximization problems."""
        # 1 out of 3 samples is optimal
        solution = create_solution(obj_values=[10.0, 20.0, 15.0], sense=Sense.MAX)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert np.isclose(result.probability_optimal, 1 / 3, rtol=0.01)
        assert result.num_optimal_found == 1
        assert result.num_samples == 3
        assert result.time_to_solution < float("inf")

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_custom_target_probability(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with custom target probability."""
        solution = create_solution(obj_values=[5.0, 10.0, 15.0], sense=Sense.MIN)

        # With 99% target probability (default)
        metric_99 = TimeToSolution(target_probability=0.99)
        result_99 = metric_99.run(solution, mock_feature_results)

        # With 90% target probability (requires fewer repetitions)
        metric_90 = TimeToSolution(target_probability=0.90)
        result_90 = metric_90.run(solution, mock_feature_results)
        assert result_90.time_to_solution < result_99.time_to_solution

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_custom_tolerance(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with custom tolerance for optimal comparison."""
        # Values close to optimal but not exactly equal
        solution = create_solution(obj_values=[5.0001, 5.0002, 10.0], sense=Sense.MIN)

        # With default tolerance (1e-6), none should match
        metric_strict = TimeToSolution(abs_tol=1e-6)
        result_strict = metric_strict.run(solution, mock_feature_results)

        # With larger tolerance (1e-3), first two should match
        metric_loose = TimeToSolution(abs_tol=1e-3)
        result_loose = metric_loose.run(solution, mock_feature_results)

        assert result_strict.num_optimal_found == 0
        assert result_loose.num_optimal_found == 2

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_single_optimal_sample(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with a single optimal sample."""
        solution = create_solution(obj_values=[5.0], sense=Sense.MIN, runtime_seconds=0.1)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 1.0
        assert result.num_optimal_found == 1
        assert result.num_samples == 1
        # When p* = 1, TTS = t_per_sample

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_single_non_optimal_sample(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with a single non-optimal sample."""
        solution = create_solution(obj_values=[10.0], sense=Sense.MIN)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 0.0
        assert result.num_optimal_found == 0
        assert result.num_samples == 1
        assert result.time_to_solution == float("inf")

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_weighted_samples(self, mock_feature_results: MagicMock) -> None:
        """Test TTS calculation with weighted samples (different counts)."""
        timer = Timer.start()
        time.sleep(0.1)
        timing = timer.stop()

        # Create solution with different counts
        # Values: [5.0, 10.0] with counts [3, 1]
        # Total samples = 4, optimal found = 3
        from luna_model import Model, Variable

        m = Model()
        with m.environment:
            x = Variable("x", vtype=Vtype.INTEGER)

        m.objective += 5 * x

        solution = Solution.from_dicts(
            data=[{"x": 1}, {"x": 2}],
            model=m,
            timing=timing,
        )

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        # Note: num_samples counts unique samples, not total count
        assert result.num_samples == 2
        # Only 1 unique sample is optimal (the one with value 5.0)
        assert result.num_optimal_found == 1
        assert result.probability_optimal == 0.5

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_low_probability_optimal(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with very low probability of finding optimal."""
        # Only 1 out of 10 samples is optimal
        obj_values = [5.0] + [10.0] * 9
        solution = create_solution(obj_values=obj_values, sense=Sense.MIN, runtime_seconds=0.1)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 0.1
        assert result.num_optimal_found == 1
        assert result.num_samples == 10
        # TTS should be higher than with higher probability
        assert result.time_to_solution > 0
        assert result.time_to_solution < float("inf")

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_high_probability_optimal(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with high probability of finding optimal (9/10)."""
        # 9 out of 10 samples are optimal
        obj_values = [5.0] * 9 + [10.0]
        solution = create_solution(obj_values=obj_values, sense=Sense.MAX, runtime_seconds=0.1)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.probability_optimal == 0.9
        assert result.num_optimal_found == 9
        assert result.num_samples == 10
        # TTS should be relatively low
        assert result.time_to_solution > 0
        assert result.time_to_solution < float("inf")

    def test_default_parameters(self) -> None:
        """Test that default parameters are set correctly."""
        metric = TimeToSolution()
        assert metric.target_probability == 0.99
        assert metric.abs_tol == 1e-6

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_tts_formula_verification(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Verify TTS formula with specific known values."""
        # 1 out of 4 samples is optimal -> p* = 0.25
        solution = create_solution(
            obj_values=[5.0, 10.0, 15.0, 20.0],
            sense=Sense.MIN,
            runtime_seconds=0.1,
        )

        metric = TimeToSolution(target_probability=0.99)
        result = metric.run(solution, mock_feature_results)

        # Manual calculation:
        # p* = 0.25
        # num_repetitions = ceil(log(1-0.99) / log(1-0.25)) = ceil(log(0.01) / log(0.75))
        # log(0.01) ≈ -4.605, log(0.75) ≈ -0.288
        # num_repetitions = ceil(16.0) = 16
        if solution.runtime is not None:
            total_runtime = solution.runtime.total_seconds
            t_per_sample = total_runtime / 4
            expected_num_reps = np.ceil(np.log(0.01) / np.log(0.75))
            expected_tts = t_per_sample * expected_num_reps

            assert result.probability_optimal == 0.25
            assert np.isclose(result.time_to_solution, expected_tts, rtol=0.01)

    @pytest.mark.parametrize("mock_feature_results", [-10.0], indirect=True)
    def test_negative_optimal_value(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with negative optimal value (valid for minimization)."""
        solution = create_solution(obj_values=[-10.0, -5.0, 0.0], sense=Sense.MIN)
        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.num_optimal_found == 1
        assert np.isclose(result.probability_optimal, 1 / 3, rtol=0.01)

    @pytest.mark.parametrize("mock_feature_results", [0.0], indirect=True)
    def test_zero_optimal_value(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test TTS with zero as optimal value."""
        solution = create_solution(obj_values=[0.0, 1.0, 2.0], sense=Sense.MIN)

        metric = TimeToSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        assert result.num_optimal_found == 1
        assert np.isclose(result.probability_optimal, 1 / 3, rtol=0.01)

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_very_low_target_probability(
        self, create_solution: SolutionFactory, mock_feature_results: MagicMock
    ) -> None:
        """Test TTS with very low target probability (50%)."""
        solution = create_solution(obj_values=[5.0, 10.0], sense=Sense.MIN)

        metric = TimeToSolution(target_probability=0.50)
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, TimeToSolutionResult)
        # With p* = 0.5 and target = 0.5, we need ceil(log(0.5)/log(0.5)) = 1 repetition
        if solution.runtime is not None:
            total_runtime = solution.runtime.total_seconds
            t_per_sample = total_runtime / 2
            assert np.isclose(result.time_to_solution, t_per_sample, rtol=0.01)

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_none_runtime_raises_value_error(
        self,
        create_solution: SolutionFactory,
        mock_feature_results: MagicMock,
    ) -> None:
        """Test that TTS raises ValueError when solution.runtime is None."""
        solution = create_solution(obj_values=[5.0], sense=Sense.MIN, set_runtime=False)

        with pytest.raises(ValueError, match="Solution runtime must not be None"):
            TimeToSolution().run(solution, mock_feature_results)
