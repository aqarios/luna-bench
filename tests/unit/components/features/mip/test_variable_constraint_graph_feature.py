"""Tests for VariableConstraintGraphFeatures extractor."""

import numpy as np
import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.variable_constraint_graph_feature import (
    VariableConstraintGraphFeatures,
    VariableConstraintGraphFeaturesResult,
)


class TestVariableConstraintGraphFeatures:
    """Test suite for VariableConstraintGraphFeatures extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, VariableConstraintGraphFeaturesResult)

        # All variables are continuous
        assert result.mean_variable_node_degree_continuous > 0
        assert result.median_variable_node_degree_continuous > 0

        # Variable node degrees should match for "all" since all are continuous
        assert result.mean_variable_node_degree_all == result.mean_variable_node_degree_continuous

        # Constraint node degrees should be computed
        assert result.mean_constraint_node_degree > 0
        assert result.median_constraint_node_degree > 0

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        # All variable types should have statistics
        assert result.mean_variable_node_degree_continuous >= 0
        assert result.mean_variable_node_degree_non_continuous >= 0
        assert result.mean_variable_node_degree_all >= 0

        # Constraint statistics
        assert result.mean_constraint_node_degree >= 0
        assert result.mean_constraint_node_degree_continuous >= 0
        assert result.mean_constraint_node_degree_non_continuous >= 0

        # Variation coefficients should be non-negative
        assert result.vc_variable_node_degree_continuous >= 0
        assert result.vc_variable_node_degree_non_continuous >= 0
        assert result.vc_variable_node_degree_all >= 0

        # Quantiles should be ordered
        assert (
            result.q10_variable_node_degree_all
            <= result.median_variable_node_degree_all
            <= result.q90_variable_node_degree_all
        )

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(empty_model)

        # All statistics should be 0 for empty model
        assert result.mean_variable_node_degree_continuous == 0.0
        assert result.mean_variable_node_degree_non_continuous == 0.0
        assert result.mean_variable_node_degree_all == 0.0
        assert result.mean_constraint_node_degree == 0.0
        assert result.median_variable_node_degree_continuous == 0.0
        assert result.median_constraint_node_degree == 0.0

    def test_sparse_model(self, sparse_model: Model) -> None:
        """Test feature extraction on a sparse model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(sparse_model)

        # Sparse model should have low node degrees
        # Many variables appear in only one or zero constraints
        assert result.mean_variable_node_degree_all < 2.0

        # Variation should be high due to sparsity
        assert result.vc_variable_node_degree_all >= 0

    def test_dense_model(self, dense_model: Model) -> None:
        """Test feature extraction on a dense model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(dense_model)

        # Dense model should have high node degrees
        # Most variables appear in most constraints
        assert result.mean_variable_node_degree_all > 2.0

        # Constraint degrees should also be high
        assert result.mean_constraint_node_degree > 2.0

    def test_variable_node_degree_calculation(self) -> None:
        """Test variable node degree calculation with known values."""
        model = Model("node_degree_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        # x appears in 2 constraints: degree = 2
        # y appears in 3 constraints: degree = 3
        # z appears in 1 constraint: degree = 1
        model.constraints += x + y <= 10
        model.constraints += x + y + z >= 5
        model.constraints += y == 3

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Mean of node degrees = (2 + 3 + 1) / 3 = 2
        assert result.mean_variable_node_degree_continuous == pytest.approx(2.0)

        # Median of [1, 2, 3] = 2
        assert result.median_variable_node_degree_continuous == pytest.approx(2.0)

    def test_constraint_node_degree_calculation(self) -> None:
        """Test constraint node degree calculation with known values."""
        model = Model("constraint_degree_test")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        # First constraint has 2 variables: degree = 2
        # Second constraint has 3 variables: degree = 3
        # Third constraint has 1 variable: degree = 1
        model.constraints += x + y <= 10
        model.constraints += x + y + z >= 5
        model.constraints += z == 3

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Mean of constraint degrees = (2 + 3 + 1) / 3 = 2
        assert result.mean_constraint_node_degree_continuous == pytest.approx(2.0)

        # Median of [1, 2, 3] = 2
        assert result.median_constraint_node_degree_continuous == pytest.approx(2.0)

    def test_continuous_only_model(self) -> None:
        """Test model with only continuous variables."""
        model = Model("continuous_only")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y
        model.constraints += x + y <= 10
        model.constraints += 2 * x + y >= 5

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Only continuous variables
        assert result.mean_variable_node_degree_continuous > 0
        assert result.mean_variable_node_degree_non_continuous == 0.0

        # All should match continuous
        assert result.mean_variable_node_degree_all == result.mean_variable_node_degree_continuous

    def test_integer_only_model(self) -> None:
        """Test model with only integer variables."""
        model = Model("integer_only")

        with model.environment:
            i1 = Variable("i1", vtype=Vtype.Integer, bounds=Bounds(0, 10))
            i2 = Variable("i2", vtype=Vtype.Binary)

        model.objective = i1 + i2
        model.constraints += i1 + i2 <= 10
        model.constraints += 2 * i1 + i2 >= 4

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Only non-continuous variables
        assert result.mean_variable_node_degree_non_continuous > 0
        assert result.mean_variable_node_degree_continuous == 0.0

        # All should match non-continuous
        assert result.mean_variable_node_degree_all == result.mean_variable_node_degree_non_continuous

    def test_quantile_ordering(self, mixed_integer_model: Model) -> None:
        """Test that quantiles are properly ordered."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        # Variable node degrees
        assert (
            result.q10_variable_node_degree_continuous
            <= result.median_variable_node_degree_continuous
            <= result.q90_variable_node_degree_continuous
        )
        assert (
            result.q10_variable_node_degree_non_continuous
            <= result.median_variable_node_degree_non_continuous
            <= result.q90_variable_node_degree_non_continuous
        )
        assert (
            result.q10_variable_node_degree_all
            <= result.median_variable_node_degree_all
            <= result.q90_variable_node_degree_all
        )

        # Constraint node degrees
        assert (
            result.q10_constraint_node_degree
            <= result.median_constraint_node_degree
            <= result.q90_constraint_node_degree
        )

    def test_variation_coefficient_validity(self, dense_model: Model) -> None:
        """Test that variation coefficients are valid."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(dense_model)

        # All variation coefficients should be non-negative
        assert result.vc_variable_node_degree_continuous >= 0
        assert result.vc_variable_node_degree_non_continuous >= 0
        assert result.vc_variable_node_degree_all >= 0
        assert result.vc_constraint_node_degree >= 0
        assert result.vc_constraint_node_degree_continuous >= 0
        assert result.vc_constraint_node_degree_non_continuous >= 0

    def test_uniform_degrees(self) -> None:
        """Test model where all variables have the same degree."""
        model = Model("uniform_degrees")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        # All variables appear in exactly 2 constraints
        model.constraints += x + y + z <= 10
        model.constraints += x + y + z >= 5

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # All variables have degree 2
        assert result.mean_variable_node_degree_continuous == 2.0
        assert result.median_variable_node_degree_continuous == 2.0

        # No variation
        assert result.vc_variable_node_degree_continuous == 0.0

        # All quantiles should be the same
        assert result.q10_variable_node_degree_continuous == 2.0
        assert result.q90_variable_node_degree_continuous == 2.0

    def test_isolated_variable(self) -> None:
        """Test handling of variable that doesn't appear in any constraint."""
        model = Model("isolated_var")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z
        # z doesn't appear in any constraint: degree = 0
        model.constraints += x + y <= 10
        model.constraints += x + y >= 5

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Degrees: x=2, y=2, z=0
        # Mean = (2 + 2 + 0) / 3 = 4/3
        assert result.mean_variable_node_degree_continuous == pytest.approx(4 / 3)

        # Median of [0, 2, 2] = 2
        assert result.median_variable_node_degree_continuous == pytest.approx(2.0)

    def test_single_variable_single_constraint(self) -> None:
        """Test edge case with single variable and single constraint."""
        model = Model("single_single")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += x <= 10

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Single variable with degree 1
        assert result.mean_variable_node_degree_continuous == 1.0
        assert result.median_variable_node_degree_continuous == 1.0

        # Single constraint with degree 1
        assert result.mean_constraint_node_degree_continuous == 1.0
        assert result.median_constraint_node_degree_continuous == 1.0

        # No variation
        assert result.vc_variable_node_degree_continuous == 0.0
        assert result.vc_constraint_node_degree_continuous == 0.0

    def test_quadratic_constraints_linear_only(self, quadratic_model: Model) -> None:
        """Test that only linear constraints are considered for graph."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(quadratic_model)

        # Should only consider linear constraints, not quadratic
        assert result.mean_variable_node_degree_all >= 0
        assert result.mean_constraint_node_degree >= 0

    def test_all_statistics_non_negative(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are non-negative."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        # All means should be non-negative
        assert result.mean_variable_node_degree_continuous >= 0
        assert result.mean_variable_node_degree_non_continuous >= 0
        assert result.mean_variable_node_degree_all >= 0
        assert result.mean_constraint_node_degree >= 0

        # All medians should be non-negative
        assert result.median_variable_node_degree_continuous >= 0
        assert result.median_variable_node_degree_non_continuous >= 0
        assert result.median_variable_node_degree_all >= 0
        assert result.median_constraint_node_degree >= 0

        # All variation coefficients should be non-negative
        assert result.vc_variable_node_degree_continuous >= 0
        assert result.vc_variable_node_degree_non_continuous >= 0
        assert result.vc_variable_node_degree_all >= 0
        assert result.vc_constraint_node_degree >= 0

        # All quantiles should be non-negative
        assert result.q10_variable_node_degree_continuous >= 0
        assert result.q90_variable_node_degree_continuous >= 0
        assert result.q10_constraint_node_degree >= 0
        assert result.q90_constraint_node_degree >= 0

    def test_deterministic_results(self, mixed_integer_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = VariableConstraintGraphFeatures()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        assert result1.mean_variable_node_degree_continuous == result2.mean_variable_node_degree_continuous
        assert result1.median_variable_node_degree_all == result2.median_variable_node_degree_all
        assert result1.vc_variable_node_degree_all == result2.vc_variable_node_degree_all
        assert result1.mean_constraint_node_degree == result2.mean_constraint_node_degree
        assert result1.q10_variable_node_degree_all == result2.q10_variable_node_degree_all
        assert result1.q90_constraint_node_degree == result2.q90_constraint_node_degree

    def test_bipartite_graph_properties(self) -> None:
        """Test that the bipartite graph structure is correctly captured."""
        model = Model("bipartite_test")

        with model.environment:
            # 3 variables
            x1 = Variable("x1", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            x2 = Variable("x2", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            x3 = Variable("x3", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x1 + x2 + x3

        # 2 constraints
        # Total edges = 5
        model.constraints += x1 + x2 <= 10  # 2 edges
        model.constraints += x2 + x3 >= 5  # 2 edges (+ 1 shared)

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # Variable degrees: x1=1, x2=2, x3=1
        # Mean = 4/3
        assert result.mean_variable_node_degree_continuous == pytest.approx(4 / 3)

        # Constraint degrees: c1=2, c2=2
        # Mean = 2
        assert result.mean_constraint_node_degree_continuous == pytest.approx(2.0)

    def test_large_degree_variation(self) -> None:
        """Test model with high variation in node degrees."""
        model = Model("high_variation")

        with model.environment:
            # Create variables with very different degrees
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            y = Variable("y", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))
            z = Variable("z", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective = x + y + z

        # x appears in 1 constraint
        # y appears in 5 constraints
        # z appears in 1 constraint
        model.constraints += x <= 10
        model.constraints += y <= 10
        model.constraints += y >= 5
        model.constraints += y <= 8
        model.constraints += y >= 2
        model.constraints += y + z == 7

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        # High variation should result in high VC
        assert result.vc_variable_node_degree_continuous > 0.5

    def test_all_values_finite(self, mixed_integer_model: Model) -> None:
        """Test that all returned values are finite."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        # Check all values are finite
        for field in vars(result):
            value = getattr(result, field)
            if isinstance(value, (int, float, np.number)):
                assert np.isfinite(value), f"Field {field} is not finite: {value}"
