"""Tests for RightHandSideFeatures extractor."""

from unittest.mock import MagicMock

import numpy as np
import pytest
from luna_model import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.features.mip.right_hand_side_feature import (
    ComparatorError,
    ConstraintSense,
    RhsStatsKey,
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
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == 10.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == 5.0

        # No equality constraints
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).std == 0.0

    def test_all_constraint_types_model(self, all_constraint_types_model: Model) -> None:
        """Test feature extraction on model with all constraint types."""
        extractor = RightHandSideFeatures()
        result = extractor.run(all_constraint_types_model)

        # All constraint types should have statistics
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean > 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean > 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean > 0

        # Standard deviations should be non-negative
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).std >= 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).std >= 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).std >= 0

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = RightHandSideFeatures()
        result = extractor.run(empty_model)

        # No statistic for empty model
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).std == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).std == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).std == 0.0

    def test_only_leq_constraints(self) -> None:
        """Test model with only <= constraints."""
        model = Model("only_leq")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 10
        model.constraints += 2 * x + y <= 15
        model.constraints += x + 2 * y <= 12

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Only leq constraints
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean > 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).std >= 0

        # Mean (10 + 15 + 12) / 3 # noqa: ERA001
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == pytest.approx(37 / 3)

        # No other constraint types
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == 0.0

    def test_only_eq_constraints(self) -> None:
        """Test model with only == constraints."""
        model = Model("only_eq")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y == 10
        model.constraints += 2 * x + y == 15

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Only eq constraints
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean > 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).std >= 0

        # Mean should be (10 + 15) / 2
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == pytest.approx(12.5)

        # No other constraint types
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == 0.0

    def test_only_geq_constraints(self) -> None:
        """Test model with only >= constraints."""
        model = Model("only_geq")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y >= 5
        model.constraints += 2 * x + y >= 8
        model.constraints += x + 2 * y >= 6

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Only geq constraints
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean > 0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).std >= 0

        # Mean should be (5 + 8 + 6) / 3
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == pytest.approx(19 / 3)

        # No other constraint types
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == 0.0

    def test_negative_rhs_values(self) -> None:
        """Test handling of negative RHS values."""
        model = Model("negative_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(Unbounded, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(Unbounded, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= -5
        model.constraints += 2 * x + y >= -10
        model.constraints += x - y == -3

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Handle negative values
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == -5.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == -10.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == -3.0

    def test_zero_rhs_values(self) -> None:
        """Test handling of zero RHS values."""
        model = Model("zero_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 0
        model.constraints += 2 * x + y >= 0
        model.constraints += x - y == 0

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Handle zero values
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == 0.0

    def test_mixed_rhs_values(self) -> None:
        """Test with mix of positive, negative, and zero RHS values."""
        model = Model("mixed_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(Unbounded, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(Unbounded, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 10
        model.constraints += 2 * x + y <= 0
        model.constraints += x - y <= -5

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Mean should be (10 + 0 + (-5)) / 3
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == pytest.approx(5 / 3)

        # Standard deviation calculation
        values = np.array([10.0, 0.0, -5.0])
        expected_std = np.std(values)
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).std == pytest.approx(expected_std)

    def test_standard_deviation_single_constraint(self) -> None:
        """Test standard deviation with single constraint (should be 0)."""
        model = Model("single_constraint")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += x <= 10

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == 10.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).std == 0.0

    def test_standard_deviation_multiple_constraints(self) -> None:
        """Test standard deviation calculation with known values."""
        model = Model("multiple_constraints")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        # RHS values: 5, 10, 15
        model.constraints += x + y >= 5
        model.constraints += 2 * x + y >= 10
        model.constraints += x + 2 * y >= 15

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # expect (5 + 10 + 15) / 3 = 10
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == pytest.approx(10.0)

        # expect std([5, 10, 15])
        expected_std = np.std([5.0, 10.0, 15.0])
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).std == pytest.approx(expected_std)

    def test_quadratic_constraints_rhs(self, quadratic_model: Model) -> None:
        """Test that RHS values are extracted from all constraint types including quadratic."""
        extractor = RightHandSideFeatures()
        result = extractor.run(quadratic_model)

        assert (
            result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean > 0
            or result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean > 0
            or result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean > 0
        )

    def test_large_rhs_values(self) -> None:
        """Test handling of large RHS values."""
        model = Model("large_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 1e10
        model.constraints += 2 * x + y >= 1e9
        model.constraints += x - y == 1e8

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == pytest.approx(1e10)
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == pytest.approx(1e9)
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == pytest.approx(1e8)

    def test_small_rhs_values(self) -> None:
        """Test handling of very small RHS values."""
        model = Model("small_rhs")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 1e-6
        model.constraints += 2 * x + y >= 1e-8
        model.constraints += x - y == 1e-10

        extractor = RightHandSideFeatures()
        result = extractor.run(model)

        # Should handle small values
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean == pytest.approx(1e-6)
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean == pytest.approx(1e-8)
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean == pytest.approx(1e-10)

    def test_all_statistics_valid(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are valid (not NaN or Inf)."""
        extractor = RightHandSideFeatures()
        result = extractor.run(mixed_integer_model)

        assert np.isfinite(result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean)
        assert np.isfinite(result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean)
        assert np.isfinite(result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean)
        assert np.isfinite(result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).std)
        assert np.isfinite(result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).std)
        assert np.isfinite(result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).std)

    def test_deterministic_results(self, all_constraint_types_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = RightHandSideFeatures()
        result1 = extractor.run(all_constraint_types_model)
        result2 = extractor.run(all_constraint_types_model)

        for sense in ConstraintSense:
            key = RhsStatsKey(constraint_sense=sense)
            assert result1.get(key).mean == result2.get(key).mean
            assert result1.get(key).std == result2.get(key).std

    def test_constraint_count_consistency(self, all_constraint_types_model: Model) -> None:
        """Test that non-zero statistics correspond to existing constraints."""
        extractor = RightHandSideFeatures()
        result = extractor.run(all_constraint_types_model)

        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ)).mean != 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.EQ)).mean != 0.0
        assert result.get(RhsStatsKey(constraint_sense=ConstraintSense.GEQ)).mean != 0.0

    def test_invalid_comparator(self) -> None:
        """Test that an invalid comparator raises an error."""
        # Create a mock constraint with an invalid comparator
        mock_constraint = MagicMock()
        mock_constraint.comparator = "INVALID"  # Not Le, Eq, or Ge
        mock_model = MagicMock()
        mock_model.constraints = [("name", mock_constraint)]

        extractor = RightHandSideFeatures()

        with pytest.raises(ComparatorError):
            extractor.run(mock_model)
