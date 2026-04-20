"""Tests for the SCIP algorithm."""

from __future__ import annotations

from luna_model import Model, Solution

from luna_bench.components.algorithms.fake_algorithm import FakeAlgorithm


class TestFakeAlgorithm:
    """Tests for the FakeAlgorithm class."""

    def test_regular_model_with_known_solution(self, regular_model: Model) -> None:
        """Test that SCIP returns the correct solution for a very simple model.

        The regular_model minimizes x + y with constraints:
        - x >= 0
        - y >= 0
        - x + y <= 10

        The optimal solution should be x = 0, y = 0 with objective value 0.
        """
        algorithm = FakeAlgorithm()
        solution = algorithm.run(regular_model)

        # Solution of correct type
        assert isinstance(solution, Solution)

    def test_timing_is_captured(self, regular_model: Model) -> None:
        """Test that timing information is properly captured and not default.

        Verifies that the solution contains timing information that is different
        from the default (zero) value.
        """
        # Configure mock to return timing > 0

        algorithm = FakeAlgorithm()
        solution = algorithm.run(regular_model)

        # Timing obect was added to solution object
        assert hasattr(solution, "runtime")
        assert solution.runtime is not None

        # Timing object values make sense
        assert solution.runtime.total_seconds > 0
        assert solution.runtime.qpu is None
