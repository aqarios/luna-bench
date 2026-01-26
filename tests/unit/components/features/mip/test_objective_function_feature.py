"""Tests for ObjectiveFunctionFeature extractor."""

import numpy as np
import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.objective_function_features import (
    NormType,
    ObjCoefStatsKey,
    ObjectiveFunctionFeature,
    ObjectiveFunctionFeatureResult,
)
from luna_bench.components.helper.var_scope import VarScope


class TestObjectiveFunctionFeature:
    """Test suite for ObjectiveFunctionFeature extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, ObjectiveFunctionFeatureResult)

        # All variables are continuous
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(2.5)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(0.5)

        # No non-continuous variables
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == 0.0

        # All variables stats should match continuous stats
        assert (
            result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).mean
            == result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean
        )
        assert (
            result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std
            == result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std
        )

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(mixed_integer_model)

        # All coefficient groups should have values
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean > 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean > 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).mean > 0

        # Standard deviations should be non-negative
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std >= 0

        # Normalized coefficients should also be computed
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.NON_CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.ALL)).mean >= 0

        # Square-root normalized coefficients
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.NON_CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.ALL)).mean >= 0

        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(3.5)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(2.5)

        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == pytest.approx(3.5)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == pytest.approx(
            np.std([5, 3, 2, 4])
        )

        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).mean == pytest.approx(3.5)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std == pytest.approx(
            np.std([5, 3, 2, 4, 1, 6])
        )

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(empty_model)

        # All features should be 0 for empty model
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std == 0.0

    def test_continuous_only_objective(self) -> None:
        """Test objective with only continuous variables."""
        model = Model("continuous_only")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 3 * x + 5 * y + 2 * z
        model.constraints += x + y + z <= 10

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Only continuous variables: |3|, |5|, |2|
        expected_mean = (3 + 5 + 2) / 3
        expected_std = np.std([3, 5, 2])

        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(expected_mean)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(expected_std)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == 0.0

    def test_integer_only_objective(self) -> None:
        """Test objective with only integer variables."""
        model = Model("integer_only")

        with model.environment:
            i1 = Variable("i1", vtype=Vtype.Integer, bounds=Bounds(0, 10))
            i2 = Variable("i2", vtype=Vtype.Integer, bounds=Bounds(0, 10))
            i3 = Variable("i3", vtype=Vtype.Binary)

        model.objective = 4 * i1 + 6 * i2 + 2 * i3
        model.constraints += i1 + i2 <= 5

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Only non-continuous variables: |4|, |6|, |2|
        expected_mean = (4 + 6 + 2) / 3
        expected_std = np.std([4, 6, 2])

        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == pytest.approx(
            expected_mean
        )
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == pytest.approx(
            expected_std
        )
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == 0.0

    def test_negative_coefficients(self) -> None:
        """Test that absolute values are correctly computed for negative coefficients."""
        model = Model("negative_coefs")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 3 * x - 5 * y  # Note the negative coefficient
        model.constraints += x + y <= 10

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Mean of absolute values: (|3| + |-5|) / 2 = 4
        # Std of |3|, |5| = 1
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(4.0)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(1.0)

    def test_normalized_coefficients(self) -> None:
        """Test normalized coefficient calculations."""
        model = Model("normalized_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 10 * x + 20 * y
        # Create constraints so variables appear in them
        model.constraints += x + y <= 5
        model.constraints += 2 * x + y >= 3

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Normalized coefficients should be computed
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).std >= 0

        # Square-root normalized should also be valid
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.CONTINUOUS)).std >= 0

    def test_sparse_objective(self, sparse_model: Model) -> None:
        """Test objective with sparse coefficients (many variables, few in objective)."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(sparse_model)

        # Objective: 2*x0 + 3*x5 + x9 (all continuous)
        # Mean: (2 + 3 + 1) / 3 = 2.0                   # noqa: ERA001
        # Std: std([2, 3, 1]) ≈ 0.816
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(2.0)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(
            np.std([2, 3, 1])
        )
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == 0.0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == 0.0

    def test_zero_coefficient_handling(self) -> None:
        """Test handling when some variables don't appear in constraints."""
        model = Model("zero_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 5 * x + 3 * y

        # Add constraint with only x
        model.constraints += x <= 10

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Should handle variables that don't appear in all constraints
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean > 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std >= 0

    def test_normalization_with_zero_constraint_coefficients(self) -> None:
        """Test normalization when a variable doesn't appear in any constraint."""
        model = Model("zero_constraint_coef")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 2 * x + 3 * y

        # Only x appears in constraint
        model.constraints += x <= 5

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Should handle normalization gracefully
        # When a variable has 0 constraint coefficients, normalization should return 0
        assert isinstance(result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).mean, float)
        assert isinstance(result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.CONTINUOUS)).mean, float)

    def test_quadratic_model_linear_objective(self, quadratic_model: Model) -> None:
        """Test that only linear objective terms are considered."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(quadratic_model)

        # Objective: x + 2*y + z (x, y continuous; z integer)
        # Continuous: |1|, |2| -> mean=1.5, std=0.5
        # Non-continuous: |1| -> mean=1.0, std=0.0
        # All: mean=(1+2+1)/3=4/3≈1.333, std≈0.471
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(1.5)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(0.5)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == pytest.approx(1.0)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std == pytest.approx(0.0)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).mean == pytest.approx(4 / 3)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std == pytest.approx(np.std([1, 2, 1]))

    def test_standard_deviation_calculation(self) -> None:
        """Test standard deviation calculation with known values."""
        model = Model("std_test")

        with model.environment:
            x1 = Variable("x1", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            x2 = Variable("x2", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            x3 = Variable("x3", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        # Coefficients: 2, 4, 6
        model.objective = 2 * x1 + 4 * x2 + 6 * x3
        model.constraints += x1 + x2 + x3 <= 10

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        # Mean = (2 + 4 + 6) / 3 = 4
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(4.0)

        # Std = np.std([2, 4, 6])               # noqa: ERA001
        expected_std = np.std([2, 4, 6])
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(expected_std)

    def test_single_variable_objective(self) -> None:
        """Test objective with single variable."""
        model = Model("single_var")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 5 * x
        model.constraints += x <= 10

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(5.0)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std == pytest.approx(
            0.0
        )  # Single value has no deviation

    def test_all_statistics_non_negative(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are non-negative."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(mixed_integer_model)

        # All means should be non-negative (absolute values)
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.NON_CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.ALL)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.NON_CONTINUOUS)).mean >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.ALL)).mean >= 0

        # All standard deviations should be non-negative
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.NON_CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.ALL)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.NON_CONTINUOUS)).std >= 0
        assert result.get(ObjCoefStatsKey(NormType.SQRT_NORMALIZED, VarScope.ALL)).std >= 0

    def test_deterministic_results(self, mixed_integer_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = ObjectiveFunctionFeature()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        assert result1.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean == pytest.approx(
            result2.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.CONTINUOUS)).mean
        )
        assert result1.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean == pytest.approx(
            result2.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.NON_CONTINUOUS)).mean
        )
        assert result1.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std == pytest.approx(
            result2.get(ObjCoefStatsKey(NormType.ABSOLUTE, VarScope.ALL)).std
        )
        assert result1.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).mean == pytest.approx(
            result2.get(ObjCoefStatsKey(NormType.NORMALIZED, VarScope.CONTINUOUS)).mean
        )
