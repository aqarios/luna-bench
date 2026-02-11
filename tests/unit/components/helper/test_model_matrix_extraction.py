"""Tests for model_matrix_extraction module."""

import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix


class TestConstraintMatrix:
    """Test suite for constraint_matrix function."""

    def test_unsupported_degree_raises_error(self) -> None:
        """Test that degree > 2 raises NotImplementedError."""
        model = Model("test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += x <= 10

        with pytest.raises(NotImplementedError, match="Degree 3 constraints are not yet supported"):
            ModelMatrix.constraint_matrix(model, degree=3, vtype=None)

    def test_quadratic_constraint_with_linear_terms(self) -> None:
        """Test quadratic constraints that include linear terms are handled correctly."""
        model = Model("quad_with_linear")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective += x + y
        # Quadratic constraint with both linear and quadratic terms: x^2 + 2x + 3y <= 10
        model.constraints += x * x + 2 * x + 3 * y <= 10

        a, b = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.QUADRATIC, vtype=None, include_b=True)

        # Should have columns for linear terms (x, y) and quadratic term (x*x)
        assert a.shape[0] == 1  # One constraint
        assert a.shape[1] == 3  # 2 linear vars + 1 quadratic pair (x*x)

        # Check RHS
        assert b[0] == 10

        # Linear coefficients should be present (x=2, y=3)
        # The exact column ordering depends on implementation
        assert 2.0 in a[0] or 3.0 in a[0]
