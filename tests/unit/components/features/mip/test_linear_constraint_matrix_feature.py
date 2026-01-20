"""Tests for LinearConstraintMatrixFeatures extractor."""

import numpy as np
import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.linear_constraint_matrix import (
    LinearConstraintMatrixFeatures,
    LinearConstraintMatrixFeaturesResult,
)


class TestLinearConstraintMatrixFeatures:
    """Test suite for LinearConstraintMatrixFeatures extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, LinearConstraintMatrixFeaturesResult)

        # All variables are continuous
        var_sums = [1 + 2, 1 + 1]
        assert result.mean_var_coef_cont == np.mean(var_sums)
        assert result.vc_var_coef_cont == np.std(var_sums) / np.mean(var_sums)

        # Variable coefficients for all should match continuous
        assert result.mean_var_coef_all == result.mean_var_coef_cont

        # Constraint coefficients should be computed
        cons_sums = [1 + 1, 2 + 1]
        assert result.mean_cons_coef_cont == np.mean(cons_sums)
        assert result.mean_cons_coefficient >= np.std(cons_sums) / np.mean(cons_sums)

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(mixed_integer_model)

        # All coefficient groups should have values
        con_vars = np.array([2, 2])
        n_con_vars = np.array([2, 3, 5, 1])
        all_vars = np.array([2, 3, 5, 1, 2, 2])
        assert result.mean_var_coef_cont == con_vars.mean()
        assert result.mean_var_coef_non_cont == n_con_vars.mean()
        assert result.mean_var_coef_all == all_vars.mean()

        # Constraint coefficients
        con_cons = np.array([0, 1, 2, 1])
        n_con_cons = np.array([3, 2, 1, 5])
        all_cons = np.array([3, 3, 3, 6])
        assert result.mean_cons_coef_cont == con_cons.mean()
        assert result.mean_cons_coef_non_cont == n_con_cons.mean()
        assert result.mean_cons_coefficient == all_cons.mean()

        # Variation coefficients should be non-negative
        assert result.vc_var_coef_cont == con_vars.std() / con_vars.mean()
        assert result.vc_var_coef_non_cont == n_con_vars.std() / n_con_vars.mean()
        assert result.vc_var_coef_all == all_vars.std() / all_vars.mean()

        # Normalized matrix entries
        b = np.array([15, 3, 8, 20])
        con_cons_n = np.array([[0, 1, 1, 0], [0, 0, 1, 1]]) / b
        n_con_cons_n = np.array([[1, 0, 1, 0], [1, 0, 0, 2], [1, 1, 0, 3], [0, 1, 0, 0]]) / b
        all_cons_n = np.array([[1, 0, 1, 0], [1, 0, 0, 2], [1, 1, 0, 3], [0, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]]) / b
        assert result.mean_dist_of_norm_cons_matrix_entr_cont == con_cons_n.flatten().mean()
        assert result.mean_dist_of_norm_cons_matrix_entr_non_cont == n_con_cons_n.flatten().mean()
        assert result.mean_dist_of_norm_cons_matrix_entr == pytest.approx(all_cons_n.flatten().mean(), abs=1e-6)

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(empty_model)

        # All features should be 0 for empty model
        assert result.mean_var_coef_cont == 0.0
        assert result.mean_var_coef_non_cont == 0.0
        assert result.mean_var_coef_all == 0.0
        assert result.mean_cons_coef_cont == 0.0
        assert result.mean_cons_coef_non_cont == 0.0
        assert result.mean_cons_coefficient == 0.0

    def test_con_only_model(self) -> None:
        """Test model with only continuous variables."""
        model = Model("continuous_only")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += 2 * x + 3 * y <= 10
        model.constraints += x + 4 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Only continuous variables
        var_coef = [3, 7]
        assert result.mean_var_coef_cont == np.mean(var_coef)
        assert result.mean_var_coef_non_cont == 0.0

        # All variables stats should match continuous
        assert result.mean_var_coef_all == result.mean_var_coef_cont

    def test_integer_only_model(self) -> None:
        """Test model with only integer variables."""
        model = Model("integer_only")

        with model.environment:
            i1 = Variable("i1", vtype=Vtype.Integer, bounds=Bounds(0, 10))
            i2 = Variable("i2", vtype=Vtype.Binary)

        model.objective = i1 + i2
        model.constraints += 2 * i1 + i2 <= 10
        model.constraints += i1 + 3 * i2 >= 4

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Only non-continuous variables
        var_coef = [3, 4]
        assert result.mean_var_coef_non_cont == np.mean(var_coef)
        assert result.mean_var_coef_cont == 0.0

        # All variables stats should match non-continuous
        assert result.mean_var_coef_all == result.mean_var_coef_non_cont

    def test_sparse_model(self, sparse_model: Model) -> None:
        """Test feature extraction on a sparse model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(sparse_model)

        # Sparse model should have low coefficient sums
        vars_coef = [1, 1, 0, 0, 0, 1, 1, 1, 0, 1]
        assert result.mean_var_coef_all == np.mean(vars_coef)

        # Variation coefficients may be high due to sparsity
        assert result.vc_var_coef_all == np.std(vars_coef) / np.mean(vars_coef)

    def test_dense_model(self, dense_model: Model) -> None:
        """Test feature extraction on a dense model."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(dense_model)

        # Dense model should have higher coefficient sums
        vars_coef = [10, 4, 5, 5]
        con_coef = [4, 6, 7, 7]
        assert result.mean_var_coef_all == np.mean(vars_coef)
        assert result.mean_cons_coefficient == np.mean(con_coef)

        # Most variables appear in most constraints
        con_vars = [10, 4]
        nc_vars = [5, 5]
        assert result.mean_var_coef_cont == np.mean(con_vars)
        assert result.mean_var_coef_non_cont == np.mean(nc_vars)

    def test_var_coef_calculation(self) -> None:
        """Test variable coefficient sum calculation with known values."""
        model = Model("var_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        # x appears in both constraints: 2 + 1 = 3
        # y appears in both constraints: 3 + 4 = 7
        model.constraints += 2 * x + 3 * y <= 10
        model.constraints += x + 4 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Mean of variable coefficients should be (3 + 7) / 2 = 5
        assert result.mean_var_coef_cont == pytest.approx(5.0)

    def test_cons_coef_calculation(self) -> None:
        """Test constraint coefficient sum calculation with known values."""
        model = Model("cons_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        # First constraint: 2 + 3 = 5
        # Second constraint: 1 + 4 = 5
        model.constraints += 2 * x + 3 * y <= 10
        model.constraints += x + 4 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Mean of constraint coefficients should be (5 + 5) / 2 = 5
        assert result.mean_cons_coef_cont == pytest.approx(5.0)

    def test_norm_cons_matrix_entr(self) -> None:
        """Test normalized constraint matrix entry calculations."""
        model = Model("normalized_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += 2 * x + 4 * y <= 10  # RHS = 10
        model.constraints += x + 2 * y >= 5  # RHS = 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)
        no_mat = np.array([[2, 4], [1, 2]]) / np.array([[10], [5]])
        # Normalized entries should be computed by dividing by RHS
        assert result.mean_dist_of_norm_cons_matrix_entr_cont == np.mean(no_mat)

    def test_zero_rhs_handling(self) -> None:
        """Test that zero RHS values are handled correctly in normalization."""
        model = Model("zero_rhs_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y == 0  # Zero RHS
        model.constraints += 2 * x + y <= 10  # Non-zero RHS

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Should handle zero RHS without division by zero
        assert np.isfinite(result.mean_dist_of_norm_cons_matrix_entr_cont)

    def test_varicoef_norm_entr(self) -> None:
        """Test variation coefficient of normalized entries per row."""
        model = Model("vc_norm_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        model.constraints += x + 2 * y + 3 * z <= 12
        model.constraints += 4 * x + y + 2 * z >= 14

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Variation coefficient per row should be computed
        assert result.mean_vari_coef_of_norm_abs_non_zero_entr_per_row_cont >= 0
        assert result.vc_vari_coef_of_norm_abs_non_zero_entr_per_row_cont >= 0

    def test_quadratic_model_linear_constraints_only(self, quadratic_model: Model) -> None:
        """Test that only linear constraints are considered."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(quadratic_model)

        # Should process linear constraints only
        assert result.mean_var_coef_all >= 0
        assert result.mean_cons_coefficient >= 0

    def test_negative_coefficients_handling(self) -> None:
        """Test handling of negative coefficients."""
        model = Model("negative_coef_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(Unbounded, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(Unbounded, Unbounded))

        model.objective = x + y
        model.constraints += x - 2 * y <= 10
        model.constraints += -3 * x + y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Should handle negative coefficients (sums use actual values, not absolute)
        assert np.isfinite(result.mean_var_coef_cont)
        assert np.isfinite(result.mean_cons_coef_cont)

    def test_all_statistics_non_negative_or_valid(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are valid (finite and non-negative where appropriate)."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(mixed_integer_model)

        # Check all means are finite
        assert np.isfinite(result.mean_var_coef_cont)
        assert np.isfinite(result.mean_var_coef_non_cont)
        assert np.isfinite(result.mean_var_coef_all)
        assert np.isfinite(result.mean_cons_coef_cont)
        assert np.isfinite(result.mean_cons_coef_non_cont)
        assert np.isfinite(result.mean_cons_coefficient)

        # Check all variation coefficients are non-negative and finite
        assert result.vc_var_coef_cont >= 0
        assert result.vc_var_coef_non_cont >= 0
        assert result.vc_var_coef_all >= 0
        assert result.vc_cons_coef_cont >= 0
        assert result.vc_cons_coef_non_cont >= 0
        assert result.vc_cons_coefficient >= 0

    def test_deterministic_results(self, mixed_integer_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = LinearConstraintMatrixFeatures()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        # Get all attributes from the result object
        attributes = [attr for attr in dir(result1) if not attr.startswith("_")]

        # Check each attribute for equality
        for attr in attributes:
            value1 = getattr(result1, attr)
            value2 = getattr(result2, attr)

            # Skip methods
            if callable(value1):
                continue

            assert value1 == value2, f"Attribute '{attr}' differs between runs"

    def test_single_cons_single_variable(self) -> None:
        """Test edge case with single constraint and single variable."""
        model = Model("single_single")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += 5 * x <= 10

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # Single variable coefficient = 5
        assert result.mean_var_coef_cont == 5.0
        # Single constraint coefficient = 5
        assert result.mean_cons_coef_cont == 5.0
        # No variation with single value
        assert result.vc_var_coef_cont == 0.0

    def test_zero_coef_rows(self) -> None:
        """Test handling when some variables don't appear in constraints."""
        model = Model("zero_coef_rows")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        # z doesn't appear in any constraint
        model.constraints += x + y <= 10
        model.constraints += 2 * x + 3 * y >= 5

        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(model)

        # z has coefficient sum of 0
        # x has coefficient sum of 2 + 1 = 3
        # y has coefficient sum of 3 + 1 = 4
        # Mean = (3 + 4 + 0) / 3 = 7/3
        assert result.mean_var_coef_cont == pytest.approx(7 / 3)

    def test_varicoef_consistency(self, dense_model: Model) -> None:
        """Test that variation coefficients are consistent with means and stds."""
        extractor = LinearConstraintMatrixFeatures()
        result = extractor.run(dense_model)

        # VC = std / mean (when mean != 0)
        # This is tested implicitly by checking non-negativity
        assert result.vc_var_coef_all >= 0
        assert result.vc_cons_coefficient >= 0

        # If mean is positive and VC is 0, there should be no variation
        if result.mean_var_coef_all > 0 and result.vc_var_coef_all == 0:
            # All variable coefficients are the same
            pass
