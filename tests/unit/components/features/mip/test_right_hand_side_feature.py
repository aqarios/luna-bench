"""Tests for RightHandSideFeatures extractor."""

import numpy as np
import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.right_hand_side_feature import (
    RightHandSideFeatures,
    RightHandSideFeaturesResult,
)


class TestRightHandSideFeatures:
    """Test suite for RightHandSideFeatures extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = RightHandSideFeatures()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, RightHandSideFeaturesResult)

        # Model has one <= and one >= constraint
        assert result.mean_right_hand_side_leq_constraints == 10.
        assert result.mean_right_hand_side_geq_constraints == 5.

        # No equality constraints
        assert result.mean_right_hand_side_eq_constraints == 0.0
        assert result.std_right_hand_side_eq_constraints == 0.0

    def test_all_constraint_types_model(self, all_constraint_types_model: Model) -> None:
        """Test feature extraction on model with all constraint types."""
        extractor = RightHandSideFeatures()
        result = extractor.run(all_constraint_types_model)

        # All constraint types should have statistics
        assert result.mean_right_hand_side_leq_constraints > 0
        assert result.mean_right_hand_side_eq_constraints > 0
        assert result.mean_right_hand_side_geq_constraints > 0

        # Standard deviations should be non-negative
        assert result.std_right_hand_side_leq_constraints >= 0
        assert result.std_right_hand_side_eq_constraints >= 0
        assert result.std_right_hand_side_geq_constraints >= 0

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = RightHandSideFeatures()
        result = extractor.run(empty_model)

        # All statistics should be 0 for empty model
        assert result.mean_right_hand_side_leq_constraints == 0.0
        assert result.mean_right_hand_side_eq_constraints == 0.0
        assert result.mean_right_hand_side_geq_constraints == 0.0
        assert result.std_right_hand_side_leq_constraints == 0.0
        assert result.std_right_hand_side_eq_constraints == 0.0
        assert result.std_right_hand_side_geq_constraints == 0.0

    def test_only_leq_constraints(self) -> None:
        """Test model with only <= constraints."""
        model = Model("only_leq")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 10
        model.constraints += 2 * x + y <= 15
        model.constraints += x + 2 * y <= 12

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Only leq constraints
        assert result.mean_right_hand_side_leq_constraints > 0
        assert result.std_right_hand_side_leq_constraints >= 0

        # Mean should be (10 + 15 + 12) / 3
        assert result.mean_right_hand_side_leq_constraints == pytest.approx(37 / 3)

        # No other constraint types
        assert result.mean_right_hand_side_eq_constraints == 0.0
        assert result.mean_right_hand_side_geq_constraints == 0.0

    def test_only_eq_constraints(self) -> None:
        """Test model with only == constraints."""
        model = Model("only_eq")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y == 10
        model.constraints += 2 * x + y == 15

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Only eq constraints
        assert result.mean_right_hand_side_eq_constraints > 0
        assert result.std_right_hand_side_eq_constraints >= 0

        # Mean should be (10 + 15) / 2
        assert result.mean_right_hand_side_eq_constraints == pytest.approx(12.5)

        # No other constraint types
        assert result.mean_right_hand_side_leq_constraints == 0.0
        assert result.mean_right_hand_side_geq_constraints == 0.0

    def test_only_geq_constraints(self) -> None:
        """Test model with only >= constraints."""
        model = Model("only_geq")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y >= 5
        model.constraints += 2 * x + y >= 8
        model.constraints += x + 2 * y >= 6

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Only geq constraints
        assert result.mean_right_hand_side_geq_constraints > 0
        assert result.std_right_hand_side_geq_constraints >= 0

        # Mean should be (5 + 8 + 6) / 3
        assert result.mean_right_hand_side_geq_constraints == pytest.approx(19 / 3)

        # No other constraint types
        assert result.mean_right_hand_side_leq_constraints == 0.0
        assert result.mean_right_hand_side_eq_constraints == 0.0

    def test_negative_rhs_values(self) -> None:
        """Test handling of negative RHS values."""
        model = Model("negative_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(Unbounded, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(Unbounded, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= -5
        model.constraints += 2 * x + y >= -10
        model.constraints += x - y == -3

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Should handle negative values
        assert result.mean_right_hand_side_leq_constraints == -5.0
        assert result.mean_right_hand_side_geq_constraints == -10.0
        assert result.mean_right_hand_side_eq_constraints == -3.0

    def test_zero_rhs_values(self) -> None:
        """Test handling of zero RHS values."""
        model = Model("zero_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 0
        model.constraints += 2 * x + y >= 0
        model.constraints += x - y == 0

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Should handle zero values
        assert result.mean_right_hand_side_leq_constraints == 0.0
        assert result.mean_right_hand_side_geq_constraints == 0.0
        assert result.mean_right_hand_side_eq_constraints == 0.0

    def test_mixed_rhs_values(self) -> None:
        """Test with mix of positive, negative, and zero RHS values."""
        model = Model("mixed_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(Unbounded, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(Unbounded, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 10
        model.constraints += 2 * x + y <= 0
        model.constraints += x - y <= -5

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Mean should be (10 + 0 + (-5)) / 3
        assert result.mean_right_hand_side_leq_constraints == pytest.approx(5 / 3)

        # Standard deviation calculation
        values = np.array([10.0, 0.0, -5.0])
        expected_std = np.std(values)
        assert result.std_right_hand_side_leq_constraints == pytest.approx(expected_std)

    def test_standard_deviation_single_constraint(self) -> None:
        """Test standard deviation with single constraint (should be 0)."""
        model = Model("single_constraint")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += x <= 10

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        assert result.mean_right_hand_side_leq_constraints == 10.0
        assert result.std_right_hand_side_leq_constraints == 0.0

    def test_standard_deviation_multiple_constraints(self) -> None:
        """Test standard deviation calculation with known values."""
        model = Model("multiple_constraints")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        # RHS values: 5, 10, 15
        model.constraints += x + y >= 5
        model.constraints += 2 * x + y >= 10
        model.constraints += x + 2 * y >= 15

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Mean = (5 + 10 + 15) / 3 = 10
        assert result.mean_right_hand_side_geq_constraints == pytest.approx(10.0)

        # Std = std([5, 10, 15])
        expected_std = np.std([5.0, 10.0, 15.0])
        assert result.std_right_hand_side_geq_constraints == pytest.approx(expected_std)

    def test_quadratic_constraints_rhs(self, quadratic_model: Model) -> None:
        """Test that RHS values are extracted from all constraint types including quadratic."""
        extractor = RightHandSideFeatures()
        result = extractor.run(quadratic_model)

        # Model should have both linear and quadratic constraints
        # The RHS extractor should process all of them
        assert (
            result.mean_right_hand_side_leq_constraints > 0
            or result.mean_right_hand_side_geq_constraints > 0
            or result.mean_right_hand_side_eq_constraints > 0
        )

    def test_large_rhs_values(self) -> None:
        """Test handling of large RHS values."""
        model = Model("large_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 1e10
        model.constraints += 2 * x + y >= 1e9
        model.constraints += x - y == 1e8

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Should handle large values
        assert result.mean_right_hand_side_leq_constraints == pytest.approx(1e10)
        assert result.mean_right_hand_side_geq_constraints == pytest.approx(1e9)
        assert result.mean_right_hand_side_eq_constraints == pytest.approx(1e8)

    def test_small_rhs_values(self) -> None:
        """Test handling of very small RHS values."""
        model = Model("small_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 1e-6
        model.constraints += 2 * x + y >= 1e-8
        model.constraints += x - y == 1e-10

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Should handle small values
        assert result.mean_right_hand_side_leq_constraints == pytest.approx(1e-6)
        assert result.mean_right_hand_side_geq_constraints == pytest.approx(1e-8)
        assert result.mean_right_hand_side_eq_constraints == pytest.approx(1e-10)

    def test_all_statistics_valid(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are valid (not NaN or Inf)."""
        extractor = RightHandSideFeatures()
        result = extractor.run(mixed_integer_model)

        # Check all values are finite
        assert np.isfinite(result.mean_right_hand_side_leq_constraints)
        assert np.isfinite(result.mean_right_hand_side_eq_constraints)
        assert np.isfinite(result.mean_right_hand_side_geq_constraints)
        assert np.isfinite(result.std_right_hand_side_leq_constraints)
        assert np.isfinite(result.std_right_hand_side_eq_constraints)
        assert np.isfinite(result.std_right_hand_side_geq_constraints)

    def test_deterministic_results(self, all_constraint_types_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = RightHandSideFeatures()
        result1 = extractor.run(all_constraint_types_model)
        result2 = extractor.run(all_constraint_types_model)

        assert result1.mean_right_hand_side_leq_constraints == result2.mean_right_hand_side_leq_constraints
        assert result1.mean_right_hand_side_eq_constraints == result2.mean_right_hand_side_eq_constraints
        assert result1.mean_right_hand_side_geq_constraints == result2.mean_right_hand_side_geq_constraints
        assert result1.std_right_hand_side_leq_constraints == result2.std_right_hand_side_leq_constraints
        assert result1.std_right_hand_side_eq_constraints == result2.std_right_hand_side_eq_constraints
        assert result1.std_right_hand_side_geq_constraints == result2.std_right_hand_side_geq_constraints

    def test_constraint_count_consistency(self, all_constraint_types_model: Model) -> None:
        """Test that non-zero statistics correspond to existing constraints."""
        extractor = RightHandSideFeatures()
        result = extractor.run(all_constraint_types_model)

        # If mean is non-zero, at least one constraint of that type should exist
        # This is implicitly tested by checking the model fixture
        # The all_constraint_types_model has 2 <= , 2 ==, and 2 >= constraints

        # All constraint types should have valid statistics
        assert result.mean_right_hand_side_leq_constraints != 0.0
        assert result.mean_right_hand_side_eq_constraints != 0.0
        assert result.mean_right_hand_side_geq_constraints != 0.0
