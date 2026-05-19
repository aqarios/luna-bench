"""Tests for the SCIP algorithm."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Any
from unittest.mock import patch

import pytest
from luna_model import Model, Solution, Variable, Vtype

from luna_bench.algorithms import ScipAlgorithm
from luna_bench.errors.infeasible_model_error import InfeasibleModelError


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

        # Solution of correct type
        assert isinstance(solution, Solution)

        best_samples = solution.best()
        assert best_samples is not None
        best_sample = best_samples[0]
        assert best_sample.obj_value == 0.0

        # Variables are in solution dict
        sample_dict = best_sample.sample.to_dict()
        assert "x" in sample_dict
        assert "y" in sample_dict

        # Both variables are 0
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

        # Timing obect was added to solution object
        assert hasattr(solution, "runtime")
        assert solution.runtime is not None

        # Timing object values make sense
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

        def tracked_tempfile(*args: Any, **kwargs: Any) -> _TemporaryFileWrapper:  # type: ignore[type-arg]
            temp = NamedTemporaryFile(*args, **kwargs)  # noqa: SIM115
            temp_file_paths.append(Path(temp.name))
            return temp

        with patch("tempfile.NamedTemporaryFile", tracked_tempfile):
            algorithm.run(regular_model)

        assert len(temp_file_paths) > 0  # temp file was created

        for temp_path in temp_file_paths:  # Check that tempfile was cleaned
            assert not temp_path.exists(), f"Temporary file {temp_path} was not cleaned up"

    def test_qubo_model_with_known_solution(self) -> None:
        """Test SCIP on a simple 3-variable QUBO.

        Minimize: -5*x0 - x1 - x2 + 2*x0*x1 + 2*x0*x2
        Unique optimal: x0=1, x1=0, x2=0 → obj = -5
        """
        model = Model(name="qubo_3var")
        with model.environment:
            x0 = Variable("x0", vtype=Vtype.BINARY)
            x1 = Variable("x1", vtype=Vtype.BINARY)
            x2 = Variable("x2", vtype=Vtype.BINARY)

        model.objective = -5 * x0 - x1 - x2 + 2 * x0 * x1 + 2 * x0 * x2
        algorithm = ScipAlgorithm()
        solution = algorithm.run(model)

        assert isinstance(solution, Solution)

        allbest = solution.best()
        assert allbest is not None
        best = allbest[0]
        assert best.obj_value == pytest.approx(-5.0)

        sample = best.sample.to_dict()
        assert sample["x0"] == pytest.approx(1.0)
        assert sample["x1"] == pytest.approx(0.0)
        assert sample["x2"] == pytest.approx(0.0)

        assert solution.runtime is not None
        assert solution.runtime.total_seconds > 0

    def test_hard_model_can_be_solved(self, hard_model: Model) -> None:
        """Test that SCIP can handle a more complex model.

        This test verifies that the algorithm can handle a harder problem
        without errors, even when returning no solution
        """
        algorithm = ScipAlgorithm(max_runtime=1)
        solution = algorithm.run(hard_model)

        # Solution object is of correct type
        assert isinstance(solution, Solution)

        # Timing object is filled despite pre-exit at max run-time
        timing = solution.runtime
        if timing is not None:
            assert timing.total_seconds > 0
