"""Tests for ObjectiveFunctionFeature extractor."""

import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.objective_function_features import (
    ObjectiveFunctionFeature,
    ObjectiveFunctionFeatureResult,
)


class TestObjectiveFunctionFeature:
    """Test suite for ObjectiveFunctionFeature extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, ObjectiveFunctionFeatureResult)

        # All variables are continuous
        assert result.mean_abscoefs_c > 0
        assert result.std_abscoefs_c >= 0

        # No non-continuous variables
        assert result.mean_abscoefs_nc == 0.0
        assert result.std_abscoefs_nc == 0.0

        # All variables stats should match continuous stats
        assert result.mean_abscoefs_v == result.mean_abscoefs_c
        assert result.std_abscoefs_v == result.std_abscoefs_c

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(mixed_integer_model)

        # All coefficient groups should have values
        assert result.mean_abscoefs_c > 0
        assert result.mean_abscoefs_nc > 0
        assert result.mean_abscoefs_v > 0

        # Standard deviations should be non-negative
        assert result.std_abscoefs_c >= 0
        assert result.std_abscoefs_nc >= 0
        assert result.std_abscoefs_v >= 0

        # Normalized coefficients should also be computed
        assert result.mean_norm_abscoefs_c >= 0
        assert result.mean_norm_abscoefs_nc >= 0
        assert result.mean_norm_abscoefs_v >= 0

        # Square-root normalized coefficients
        assert result.mean_sqrtnorm_abscoefs_c >= 0
        assert result.mean_sqrtnorm_abscoefs_nc >= 0
        assert result.mean_sqrtnorm_abscoefs_v >= 0

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(empty_model)

        # All features should be 0 for empty model
        assert result.mean_abscoefs_c == 0.0
        assert result.mean_abscoefs_nc == 0.0
        assert result.mean_abscoefs_v == 0.0
        assert result.std_abscoefs_c == 0.0
        assert result.std_abscoefs_nc == 0.0
        assert result.std_abscoefs_v == 0.0

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

        # Only continuous variables
        assert result.mean_abscoefs_c > 0
        assert result.mean_abscoefs_nc == 0.0

        # Check mean calculation
        expected_mean = (3 + 5 + 2) / 3
        assert result.mean_abscoefs_c == pytest.approx(expected_mean)

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

        # Only non-continuous variables
        assert result.mean_abscoefs_nc > 0
        assert result.mean_abscoefs_c == 0.0

        # Check mean calculation
        expected_mean = (4 + 6 + 2) / 3
        assert result.mean_abscoefs_nc == pytest.approx(expected_mean)

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

        # Mean of absolute values should be (3 + 5) / 2 = 4
        assert result.mean_abscoefs_c == pytest.approx(4.0)

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
        assert result.mean_norm_abscoefs_c >= 0
        assert result.std_norm_abscoefs_c >= 0

        # Square-root normalized should also be valid
        assert result.mean_sqrtnorm_abscoefs_c >= 0
        assert result.std_sqrtnorm_abscoefs_c >= 0

    def test_sparse_objective(self, sparse_model: Model) -> None:
        """Test objective with sparse coefficients (many variables, few in objective)."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(sparse_model)

        # Should only consider variables in the objective
        assert result.mean_abscoefs_c > 0

        # All objective variables are continuous in sparse_model
        assert result.mean_abscoefs_nc == 0.0

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
        assert result.mean_abscoefs_c > 0
        assert result.std_abscoefs_c >= 0

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
        assert isinstance(result.mean_norm_abscoefs_c, float)
        assert isinstance(result.mean_sqrtnorm_abscoefs_c, float)

    def test_quadratic_model_linear_objective(self, quadratic_model: Model) -> None:
        """Test that only linear objective terms are considered."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(quadratic_model)

        # Should only consider linear terms in objective
        assert result.mean_abscoefs_c > 0 or result.mean_abscoefs_nc > 0
        assert result.mean_abscoefs_v > 0

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
        assert result.mean_abscoefs_c == pytest.approx(4.0)

        # Std = sqrt(((2-4)^2 + (4-4)^2 + (6-4)^2) / 3) = sqrt(8/3) ≈ 1.633
        import numpy as np

        expected_std = np.std([2, 4, 6])
        assert result.std_abscoefs_c == pytest.approx(expected_std)

    def test_single_variable_objective(self) -> None:
        """Test objective with single variable."""
        model = Model("single_var")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = 5 * x
        model.constraints += x <= 10

        extractor = ObjectiveFunctionFeature()
        result = extractor.run(model)

        assert result.mean_abscoefs_c == 5.0
        assert result.std_abscoefs_c == 0.0  # Single value has no deviation

    def test_all_statistics_non_negative(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are non-negative."""
        extractor = ObjectiveFunctionFeature()
        result = extractor.run(mixed_integer_model)

        # All means should be non-negative (absolute values)
        assert result.mean_abscoefs_c >= 0
        assert result.mean_abscoefs_nc >= 0
        assert result.mean_abscoefs_v >= 0
        assert result.mean_norm_abscoefs_c >= 0
        assert result.mean_norm_abscoefs_nc >= 0
        assert result.mean_norm_abscoefs_v >= 0
        assert result.mean_sqrtnorm_abscoefs_c >= 0
        assert result.mean_sqrtnorm_abscoefs_nc >= 0
        assert result.mean_sqrtnorm_abscoefs_v >= 0

        # All standard deviations should be non-negative
        assert result.std_abscoefs_c >= 0
        assert result.std_abscoefs_nc >= 0
        assert result.std_abscoefs_v >= 0
        assert result.std_norm_abscoefs_c >= 0
        assert result.std_norm_abscoefs_nc >= 0
        assert result.std_norm_abscoefs_v >= 0
        assert result.std_sqrtnorm_abscoefs_c >= 0
        assert result.std_sqrtnorm_abscoefs_nc >= 0
        assert result.std_sqrtnorm_abscoefs_v >= 0

    def test_deterministic_results(self, mixed_integer_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = ObjectiveFunctionFeature()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        assert result1.mean_abscoefs_c == result2.mean_abscoefs_c
        assert result1.mean_abscoefs_nc == result2.mean_abscoefs_nc
        assert result1.std_abscoefs_v == result2.std_abscoefs_v
        assert result1.mean_norm_abscoefs_c == result2.mean_norm_abscoefs_c
