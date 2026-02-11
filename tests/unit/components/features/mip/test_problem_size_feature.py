"""Tests for ProblemSizeFeatures extractor."""

from unittest.mock import MagicMock

import pytest
from luna_quantum import Bounds, Model, Variable, Vtype, quicksum

from luna_bench.components.features.mip.problem_size_feature import (
    ModelBoundsError,
    ProblemSizeFeatures,
    ProblemSizeFeaturesResult,
    VarType,
    VarTypeKey,
)


class TestProblemSizeFeatures:
    """Test suite for ProblemSizeFeatures extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, ProblemSizeFeaturesResult)
        assert result.num_vars == 2
        assert result.num_constraints == 2
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).count == 2
        assert result.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).count == 0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.INTEGER)).count == 0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).fraction == 1.0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).fraction == 0.0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.NON_CONTINUOUS)).count == 0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.UNBOUNDED_NON_CONTINUOUS)).count == 0

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(mixed_integer_model)

        assert result.num_vars == 6
        assert result.num_constraints == 4
        assert result.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).count == 2
        assert result.var_counts.get(VarTypeKey(var_type=VarType.INTEGER)).count == 2
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).count == 2
        assert result.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).fraction == pytest.approx(2 / 6)
        assert result.var_counts.get(VarTypeKey(var_type=VarType.INTEGER)).fraction == pytest.approx(2 / 6)
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).fraction == pytest.approx(2 / 6)
        assert result.var_counts.get(VarTypeKey(var_type=VarType.NON_CONTINUOUS)).count == 4
        assert result.var_counts.get(VarTypeKey(var_type=VarType.NON_CONTINUOUS)).fraction == pytest.approx(4 / 6)
        assert result.var_counts.get(VarTypeKey(var_type=VarType.UNBOUNDED_NON_CONTINUOUS)).count == 1

    def test_quadratic_model(self, quadratic_model: Model) -> None:
        """Test feature extraction on a model with quadratic constraints."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(quadratic_model)

        assert result.num_vars == 3
        assert result.num_constraints == 4
        assert result.num_quadratic_constraints == 2
        assert result.num_non_zero_entries_quadratic_constraint_matrix > 0

        # Check that linear constraint matrix has non-zero entries
        assert result.num_non_zero_entries_linear_constraint_matrix > 0

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(empty_model)

        assert result.num_vars == 0
        assert result.num_constraints == 0
        assert result.num_non_zero_entries_linear_constraint_matrix == 0
        assert result.num_quadratic_constraints == 0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).fraction == 0.0
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).fraction == 0.0
        assert result.support_size.mean == 0.0
        assert result.support_size.median == 0.0

    def test_sparse_model(self, sparse_model: Model) -> None:
        """Test feature extraction on a sparse model."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(sparse_model)

        assert result.num_vars == 6  # only active vars considered
        assert result.num_constraints == 3
        total_possible_entries = result.num_vars * result.num_constraints
        sparsity_ratio = result.num_non_zero_entries_linear_constraint_matrix / total_possible_entries
        assert sparsity_ratio < 0.5  # Should be sparse

    def test_dense_model(self, dense_model: Model) -> None:
        """Test feature extraction on a dense model."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(dense_model)

        assert result.num_vars == 4
        assert result.num_constraints == 4

        # Check density
        total_possible_entries = result.num_vars * result.num_constraints
        density_ratio = result.num_non_zero_entries_linear_constraint_matrix / total_possible_entries
        assert density_ratio > 0.8  # Should be dense

    def test_unbounded_variables_model(self, unbounded_variables_model: Model) -> None:
        """Test feature extraction with unbounded variables."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(unbounded_variables_model)

        assert result.num_vars == 4
        assert result.var_counts.get(VarTypeKey(var_type=VarType.INTEGER)).count == 3
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).count == 1
        assert result.var_counts.get(VarTypeKey(var_type=VarType.UNBOUNDED_NON_CONTINUOUS)).count == 1
        assert result.var_counts.get(VarTypeKey(var_type=VarType.UNBOUNDED_NON_CONTINUOUS)).fraction == pytest.approx(
            1 / 4
        )

    def test_support_sizes(self, mixed_integer_model: Model) -> None:
        """Test support size calculations for bounded variables."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(mixed_integer_model)

        # Binary variables have support size 2 (0 or 1)
        # i1 has bounds (0, 10) so support size is 11

        # Support sizes should be calculated
        assert result.support_size.mean == pytest.approx((2 + 2 + 11) / 3)
        assert result.support_size.median == pytest.approx(2)

        # Variation coefficient should be non-negative
        assert result.support_size.variation_coefficient >= 0

        # Quantiles should be ordered
        assert result.support_size.q10 <= result.support_size.median <= result.support_size.q90

    def test_semi_continuous_semi_integer_variables(self) -> None:
        """Test handling of semi-continuous and semi-integer variables."""
        from luna_quantum import Vtype

        model = Model("semi_vars")
        with model.environment:
            # Semi-continuous: can be 0 or in [lb, ub]
            sc = Variable("sc", vtype=Vtype.Real, bounds=Bounds(5, 10))

            # Semi-integer: can be 0 or integer in [lb, ub]
            si = Variable("si", vtype=Vtype.Integer, bounds=Bounds(3, 8))

        model.objective = sc + si
        model.constraints += sc + si <= 15

        extractor = ProblemSizeFeatures()
        result = extractor.run(model)

        assert result.num_vars == 2
        assert result.var_counts.get(VarTypeKey(var_type=VarType.SEMI_CONTINUOUS)).count == 0  # not implemented
        assert result.var_counts.get(VarTypeKey(var_type=VarType.SEMI_INTEGER)).count == 0  # not implemented
        assert result.var_counts.get(VarTypeKey(var_type=VarType.SEMI_CONTINUOUS)).fraction == pytest.approx(0)
        assert result.var_counts.get(VarTypeKey(var_type=VarType.SEMI_INTEGER)).fraction == pytest.approx(0)

    def test_variable_type_fractions_sum_to_one(self, mixed_integer_model: Model) -> None:
        """Test that all variable type fractions sum to 1."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(mixed_integer_model)

        total_fraction = (
            result.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).fraction
            + result.var_counts.get(VarTypeKey(var_type=VarType.INTEGER)).fraction
            + result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).fraction
            + result.var_counts.get(VarTypeKey(var_type=VarType.SEMI_CONTINUOUS)).fraction
            + result.var_counts.get(VarTypeKey(var_type=VarType.SEMI_INTEGER)).fraction
        )

        assert total_fraction == pytest.approx(1.0)

    def test_non_zero_entries_consistency(self, dense_model: Model) -> None:
        """Test that non-zero entry counts are consistent."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(dense_model)

        # Non-zero entries should not exceed matrix size
        max_entries = result.num_vars * result.num_constraints
        assert result.num_non_zero_entries_linear_constraint_matrix <= max_entries

    def test_support_size_statistics_validity(self, mixed_integer_model: Model) -> None:
        """Test that support size statistics are valid."""
        extractor = ProblemSizeFeatures()
        result = extractor.run(mixed_integer_model)

        # All statistics should be non-negative
        assert result.support_size.mean >= 0
        assert result.support_size.median >= 0
        assert result.support_size.variation_coefficient >= 0
        assert result.support_size.q10 >= 0
        assert result.support_size.q90 >= 0

        # Mean and median should be reasonable
        if result.support_size.mean > 0:
            assert result.support_size.median > 0

    def test_multiple_runs_deterministic(self, mixed_integer_model: Model) -> None:
        """Test that running the extractor multiple times gives consistent results."""
        extractor = ProblemSizeFeatures()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        assert result1.num_vars == result2.num_vars
        assert result1.num_constraints == result2.num_constraints
        assert (
            result1.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).count
            == result2.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).count
        )
        assert result1.support_size.mean == result2.support_size.mean

    def test_large_model_performance(self) -> None:
        """Test that the extractor handles larger models efficiently."""
        from luna_quantum import Unbounded, Vtype

        model = Model("large_model")

        with model.environment:
            # Create 100 variables
            variables = [Variable(f"x{i}", vtype=Vtype.Real, bounds=Bounds(0, Unbounded)) for i in range(100)]

        model.objective += quicksum(variables)

        # Create 50 constraints
        for i in range(50):
            model.constraints += quicksum(variables[j] for j in range(i, min(i + 10, 100))) <= 100

        extractor = ProblemSizeFeatures()
        result = extractor.run(model)

        assert result.num_vars == 100
        assert result.num_constraints == 50
        assert result.var_counts.get(VarTypeKey(var_type=VarType.CONTINUOUS)).count == 100

    @pytest.mark.parametrize("vtype", [Vtype.Integer, Vtype.Real])
    def test_none_bounds_raises_model_bounds_error(self, vtype: Vtype) -> None:
        """Test that None bounds raise ModelBoundsError for integer and real variables."""
        magic_model = MagicMock()
        mock_var = MagicMock()
        mock_var.vtype = vtype
        mock_var.bounds.lower = None
        mock_var.bounds.upper = None
        magic_model.variables.return_value = [mock_var]
        magic_model.num_variables = 1
        magic_model.num_constraints = 0
        magic_model.constraints = []
        magic_model.name = "test_model"

        extractor = ProblemSizeFeatures()

        with pytest.raises(ModelBoundsError, match=r"\(model: test_model\) \(expected: \[-inf, inf\]\)"):
            extractor.run(model=magic_model)
