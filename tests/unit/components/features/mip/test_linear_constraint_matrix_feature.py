"""Tests for LinearConstraintMatrixFeatures extractor."""

import numpy as np
import pytest
from luna_model import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.linear_constraint_matrix import (
    CoefStatsKey,
    CoefType,
    LinearConstraintMatrixFeatures,
    LinearConstraintMatrixFeaturesResult,
)
from luna_bench.components.helper.var_scope import VarScope


class TestLinearConstraintMatrixFeatures:
    """Test suite for LinearConstraintMatrixFeatures extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, LinearConstraintMatrixFeaturesResult)

        # All variables in linear-model are continuous
        var_sums = [1 + 2, 1 + 1]
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == np.mean(var_sums)
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).variation_coefficient == np.std(
            var_sums
        ) / np.mean(var_sums)

        # Variable coefficients for all should match continuous
        assert (
            result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean
            == result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean
        )

        cons_sums = [1 + 1, 2 + 1]
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean == np.mean(cons_sums)
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).mean >= np.std(cons_sums) / np.mean(
            cons_sums
        )

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(mixed_integer_model)

        con_vars = np.array([2, 2])
        n_con_vars = np.array([2, 3, 5, 1])
        all_vars = np.array([2, 3, 5, 1, 2, 2])
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == con_vars.mean()
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean == n_con_vars.mean()
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean == all_vars.mean()

        con_cons = np.array([0, 1, 2, 1])
        n_con_cons = np.array([3, 2, 1, 5])
        all_cons = np.array([3, 3, 3, 6])
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean == con_cons.mean()
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.NON_CONTINUOUS)).mean == n_con_cons.mean()
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).mean == all_cons.mean()

        assert (
            result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).variation_coefficient
            == con_vars.std() / con_vars.mean()
        )
        assert (
            result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).variation_coefficient
            == n_con_vars.std() / n_con_vars.mean()
        )
        assert (
            result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).variation_coefficient
            == all_vars.std() / all_vars.mean()
        )

        # Normalized matrix entries
        b = np.array([15, 3, 8, 20])
        con_cons_n = np.array([[0, 1, 1, 0], [0, 0, 1, 1]]) / b
        n_con_cons_n = np.array([[1, 0, 1, 0], [1, 0, 0, 2], [1, 1, 0, 3], [0, 1, 0, 0]]) / b
        all_cons_n = np.array([[1, 0, 1, 0], [1, 0, 0, 2], [1, 1, 0, 3], [0, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]]) / b
        assert result.get(CoefStatsKey(CoefType.NORMALIZED, VarScope.CONTINUOUS)).mean == con_cons_n.flatten().mean()
        assert (
            result.get(CoefStatsKey(CoefType.NORMALIZED, VarScope.NON_CONTINUOUS)).mean == n_con_cons_n.flatten().mean()
        )
        assert result.get(CoefStatsKey(CoefType.NORMALIZED, VarScope.ALL)).mean == pytest.approx(
            all_cons_n.flatten().mean(), abs=1e-6
        )

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(empty_model)

        # All features should be 0 for empty model
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == 0.0
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean == 0.0
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean == 0.0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean == 0.0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.NON_CONTINUOUS)).mean == 0.0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).mean == 0.0

    def test_con_only_model(self) -> None:
        """Test model with only continuous variables."""
        model = Model("continuous_only")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += 2 * x + 3 * y <= 10
        model.constraints += x + 4 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Only continuous variables
        var_coef = [3, 7]
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == np.mean(var_coef)
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean == 0.0

        # As continuous_vars == model_vars, need to match
        assert (
            result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean
            == result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean
        )

    def test_integer_only_model(self) -> None:
        """Test model with only integer variables."""
        model = Model("integer_only")

        with model.environment:
            i1 = Variable("i1", vtype=Vtype.INTEGER, bounds=Bounds(0, 10))
            i2 = Variable("i2", vtype=Vtype.BINARY)

        model.objective = i1 + i2
        model.constraints += 2 * i1 + i2 <= 10
        model.constraints += i1 + 3 * i2 >= 4

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        var_coef = [3, 4]
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean == np.mean(var_coef)
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == 0.0

        assert (
            result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean
            == result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean
        )

    def test_sparse_model(self, sparse_model: Model) -> None:
        """Test feature extraction on a sparse model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(sparse_model)

        vars_coef = [1, 1, 0, 0, 0, 1, 1, 1, 0, 1]
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean == np.mean(vars_coef)

        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).variation_coefficient == np.std(
            vars_coef
        ) / np.mean(vars_coef)

    def test_dense_model(self, dense_model: Model) -> None:
        """Test feature extraction on a dense model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(dense_model)

        vars_coef = [10, 4, 5, 5]
        con_coef = [4, 6, 7, 7]
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean == np.mean(vars_coef)
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).mean == np.mean(con_coef)

        con_vars = [10, 4]
        nc_vars = [5, 5]
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == np.mean(con_vars)
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean == np.mean(nc_vars)

    def test_var_coef_calculation(self) -> None:
        """Test variable coefficient sum calculation with known values."""
        model = Model("var_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += 2 * x + 3 * y <= 10
        model.constraints += x + 4 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Mean of variable coefficients should be (3 + 7) / 2 = 5, see sum row of constraints
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == pytest.approx(5.0)

    def test_cons_coef_calculation(self) -> None:
        """Test constraint coefficient sum calculation with known values."""
        model = Model("cons_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += 2 * x + 3 * y <= 10
        model.constraints += x + 4 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Mean of constraint coefficients should be (5 + 5) / 2 = 5, see sum of constriant rows
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean == pytest.approx(5.0)

    def test_norm_cons_matrix_entr(self) -> None:
        """Test normalized constraint matrix entry calculations."""
        model = Model("normalized_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += 2 * x + 4 * y <= 10
        model.constraints += x + 2 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)
        no_mat = np.array([[2, 4], [1, 2]]) / np.array([[10], [5]])
        # Normalized entries should be computed by dividing by RHS
        assert result.get(CoefStatsKey(CoefType.NORMALIZED, VarScope.CONTINUOUS)).mean == np.mean(no_mat)

    def test_zero_rhs_handling(self) -> None:
        """Test that zero RHS values are handled correctly in normalization."""
        model = Model("zero_rhs_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y == 0
        model.constraints += 2 * x + y <= 10

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Should handle zero RHS without division by zero
        assert np.isfinite(result.get(CoefStatsKey(CoefType.NORMALIZED, VarScope.CONTINUOUS)).mean)

    def test_varicoef_norm_entr(self) -> None:
        """Test variation coefficient of normalized entries per row."""
        model = Model("vc_norm_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        model.constraints += x + 2 * y + 3 * z <= 12
        model.constraints += 4 * x + y + 2 * z >= 14

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Variation coefficient per row should be computed
        assert result.get(CoefStatsKey(CoefType.ROW_VARIATION, VarScope.CONTINUOUS)).mean >= 0
        assert result.get(CoefStatsKey(CoefType.ROW_VARIATION, VarScope.CONTINUOUS)).variation_coefficient >= 0

    def test_quadratic_model_linear_constraints_only(self, quadratic_model: Model) -> None:
        """Test that only linear constraints are considered."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(quadratic_model)

        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean >= 0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).mean >= 0

    def test_negative_coefficients_handling(self) -> None:
        """Test handling of negative coefficients."""
        model = Model("negative_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(Unbounded, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(Unbounded, Unbounded))

        model.objective = x + y
        model.constraints += x - 2 * y <= 10
        model.constraints += -3 * x + y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Should handle negative coefficients (sums use actual values, not absolute)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean)

    def test_all_statistics_non_negative_or_valid(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are valid (finite and non-negative where appropriate)."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(mixed_integer_model)

        # Check all means are finite
        assert np.isfinite(result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).mean)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.NON_CONTINUOUS)).mean)
        assert np.isfinite(result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).mean)

        # Check all variation coefficients are non-negative and finite
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).variation_coefficient >= 0
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.NON_CONTINUOUS)).variation_coefficient >= 0
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).variation_coefficient >= 0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).variation_coefficient >= 0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.NON_CONTINUOUS)).variation_coefficient >= 0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).variation_coefficient >= 0

    def test_deterministic_results(self, mixed_integer_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = LinearConstraintMatrixFeatures()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        # Check all stats match
        for key in result1.stats:
            assert result1.stats[key].mean == result2.stats[key].mean
            assert result1.stats[key].variation_coefficient == result2.stats[key].variation_coefficient

    def test_single_cons_single_variable(self) -> None:
        """Test edge case with single constraint and single variable."""
        model = Model("single_single")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += 5 * x <= 10

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == 5.0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.CONTINUOUS)).mean == 5.0
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).variation_coefficient == 0.0

    def test_zero_coef_rows(self) -> None:
        """Test handling when some variables don't appear in constraints."""
        model = Model("zero_coef_rows")

        with model.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.REAL, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        # z doesn't appear in any constraint
        model.constraints += x + y <= 10
        model.constraints += 2 * x + 3 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # z has coefficient sum of 0
        # x has coefficient sum of 2 + 1 = 3
        # y has coefficient sum of 3 + 1 = 4
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean == pytest.approx(7 / 3)

    def test_varicoef_consistency(self, dense_model: Model) -> None:
        """Test that variation coefficients are consistent with means and stds."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(dense_model)
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).variation_coefficient >= 0
        assert result.get(CoefStatsKey(CoefType.CONSTRAINT, VarScope.ALL)).variation_coefficient >= 0

        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).mean == pytest.approx(6)
        assert result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.ALL)).variation_coefficient == pytest.approx(
            (np.sqrt(6 / 4) / 6), rel=1e-3
        )

    def test_get_accessor(self, mixed_integer_model: Model) -> None:
        """Test the get accessor method returns correct CoefStats."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(mixed_integer_model)

        stats = result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS))
        assert stats.mean == result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).mean
        assert (
            stats.variation_coefficient
            == result.get(CoefStatsKey(CoefType.VARIABLE, VarScope.CONTINUOUS)).variation_coefficient
        )
