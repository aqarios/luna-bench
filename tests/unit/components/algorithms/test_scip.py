"""Tests for the SCIP algorithm."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from tempfile import NamedTemporaryFile

    from luna_quantum import Model


from luna_quantum import Solution

from luna_bench.components.algorithms.scip import InfeasibleModelError, ScipAlgorithm


class TestScipAlgorithm:
    """Tests for the ScipAlgorithm class."""

    def test_regular_model_with_known_solution(self, regular_model: Model) -> None:
        """Test that SCIP returns the correct solution for a very simple model.

        The regular_model minimizes x + y with constraints:
        - x >= 0
        - y >= 0
        - x + y <= 10

        The optimal solution should be x = 0, y = 0 with objective value 0.
        """
        algorithm = ScipAlgorithm()
        solution = algorithm.run(regular_model)

        # Verify solution type
        assert isinstance(solution, Solution)

        # Verify the objective value is correct
        best_sample = solution.best()
        assert best_sample.obj_value == 0.0

        # Verify the solution contains the correct variables
        sample_dict = best_sample.sample.to_dict()
        assert "x" in sample_dict
        assert "y" in sample_dict

        # Verify the values are optimal (both should be 0)
        assert sample_dict["x"] == 0.0
        assert sample_dict["y"] == 0.0

    def test_infeasible_model_raises_error(self, infeasible_model: Model) -> None:
        """Test that SCIP raises InfeasibleModelError for infeasible models.

        The infeasible_model has contradictory constraints:
        - x >= 10
        - x <= 5

        Which is impossible to satisfy.
        """
        algorithm = ScipAlgorithm(max_runtime=10)

        with pytest.raises(InfeasibleModelError):
            algorithm.run(infeasible_model)

    def test_timing_is_captured(self, regular_model: Model) -> None:
        """Test that timing information is properly captured and not default.

        Verifies that the solution contains timing information that is different
        from the default (zero) value.
        """
        # Configure mock to return timing > 0

        algorithm = ScipAlgorithm(max_runtime=10)
        solution = algorithm.run(regular_model)

        # Verify timing is present
        assert hasattr(solution, "runtime")
        assert solution.runtime is not None

        # Verify timing is not the default value (0)
        # The solver should take some non-zero time to execute
        assert solution.runtime.total_seconds > 0
        assert solution.runtime.qpu is None

    def test_temporary_file_cleanup(self, regular_model: Model) -> None:
        """Test that temporary LP files are cleaned up after solving.

        Verifies that the temporary file created during the solving process
        is properly deleted after the algorithm completes.
        """
        algorithm = ScipAlgorithm(max_runtime=1)
        temp_file_paths: list[Path] = []

        # Patch NamedTemporaryFile to track the temporary file path
        original_tempfile = __import__("tempfile").NamedTemporaryFile

        def tracked_tempfile(*args: Any, **kwargs: Any) -> NamedTemporaryFile:
            temp = original_tempfile(*args, **kwargs)
            temp_file_paths.append(Path(temp.name))
            return temp

        with patch("tempfile.NamedTemporaryFile", tracked_tempfile):
            solution = algorithm.run(regular_model)

        # Verify that a temporary file was created
        assert len(temp_file_paths) > 0

        # Verify that all temporary files were cleaned up
        for temp_path in temp_file_paths:
            assert not temp_path.exists(), f"Temporary file {temp_path} was not cleaned up"

        # Verify solution is still valid
        assert isinstance(solution, Solution)

    def test_hard_model_can_be_solved(self, hard_model: Model) -> None:
        """Test that SCIP can handle a more complex model.

        This test verifies that the algorithm can handle a harder problem
        without errors, even when returning no solution
        """
        algorithm = ScipAlgorithm(max_runtime=1)
        solution = algorithm.run(hard_model)

        # Verify solution is returned
        assert isinstance(solution, Solution)

        # Verify timing was recorded
        assert solution.runtime.total_seconds > 0

        # If a solution was found, verify it has an objective value
        best_sample = solution.best()
        if best_sample is not None:
            assert isinstance(best_sample.obj_value, float)
