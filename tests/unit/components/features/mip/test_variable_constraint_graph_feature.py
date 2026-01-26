"""Tests for VariableConstraintGraphFeatures extractor."""

import numpy as np
import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype

from luna_bench.components.features.mip.variable_constraint_graph_feature import (
    NodeDegreeStatsKey,
    NodeType,
    VariableConstraintGraphFeatures,
    VariableConstraintGraphFeaturesResult,
)
from luna_bench.components.helper.var_scope import VarScope


class TestVariableConstraintGraphFeatures:
    """Test suite for VariableConstraintGraphFeatures extractor."""

    def test_simple_linear_model(self, simple_linear_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(simple_linear_model)

        assert isinstance(result, VariableConstraintGraphFeaturesResult)

        # All variables are continuous
        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        assert var_cont.mean > 0
        assert var_cont.median > 0

        # Variable node degrees should match for "all" since all are continuous
        assert var_all.mean == var_cont.mean

        # Constraint node degrees should be computed
        assert cons_all.mean > 0
        assert cons_all.median > 0

    def test_mixed_integer_model(self, mixed_integer_model: Model) -> None:
        """Test feature extraction on a mixed-integer model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.CONTINUOUS))
        cons_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.NON_CONTINUOUS))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # All variable types should have statistics
        assert var_cont.mean >= 0
        assert var_nc.mean >= 0
        assert var_all.mean >= 0

        # Constraint statistics
        assert cons_all.mean >= 0
        assert cons_cont.mean >= 0
        assert cons_nc.mean >= 0

        # Variation coefficients should be non-negative
        assert var_cont.variation_coefficient >= 0
        assert var_nc.variation_coefficient >= 0
        assert var_all.variation_coefficient >= 0

        # Quantiles should be ordered
        assert var_all.q10 <= var_all.median <= var_all.q90

    def test_empty_model(self, empty_model: Model) -> None:
        """Test feature extraction on an empty model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(empty_model)

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # All statistics should be 0 for empty model
        assert var_cont.mean == 0.0
        assert var_nc.mean == 0.0
        assert var_all.mean == 0.0
        assert cons_all.mean == 0.0
        assert var_cont.median == 0.0
        assert cons_all.median == 0.0

    def test_sparse_model(self, sparse_model: Model) -> None:
        """Test feature extraction on a sparse model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(sparse_model)

        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))

        # Sparse model should have low node degrees
        # Many variables appear in only one or zero constraints
        assert var_all.mean < 2.0

        # Variation should be high due to sparsity
        assert var_all.variation_coefficient >= 0

    def test_dense_model(self, dense_model: Model) -> None:
        """Test feature extraction on a dense model."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(dense_model)

        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # Dense model should have high node degrees
        # Most variables appear in most constraints
        assert var_all.mean > 2.0

        # Constraint degrees should also be high
        assert cons_all.mean > 2.0

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))

        # Mean of node degrees = (2 + 3 + 1) / 3 = 2
        assert var_cont.mean == pytest.approx(2.0)

        # Median of [1, 2, 3] = 2
        assert var_cont.median == pytest.approx(2.0)

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

        cons_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.CONTINUOUS))

        # Mean of constraint degrees = (2 + 3 + 1) / 3 = 2
        assert cons_cont.mean == pytest.approx(2.0)

        # Median of [1, 2, 3] = 2
        assert cons_cont.median == pytest.approx(2.0)

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))

        # Only continuous variables
        assert var_cont.mean > 0
        assert var_nc.mean == 0.0

        # All should match continuous
        assert var_all.mean == var_cont.mean

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))

        # Only non-continuous variables
        assert var_nc.mean > 0
        assert var_cont.mean == 0.0

        # All should match non-continuous
        assert var_all.mean == var_nc.mean

    def test_quantile_ordering(self, mixed_integer_model: Model) -> None:
        """Test that quantiles are properly ordered."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # Variable node degrees
        assert var_cont.q10 <= var_cont.median <= var_cont.q90
        assert var_nc.q10 <= var_nc.median <= var_nc.q90
        assert var_all.q10 <= var_all.median <= var_all.q90

        # Constraint node degrees
        assert cons_all.q10 <= cons_all.median <= cons_all.q90

    def test_variation_coefficient_validity(self, dense_model: Model) -> None:
        """Test that variation coefficients are valid."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(dense_model)

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.CONTINUOUS))
        cons_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.NON_CONTINUOUS))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # All variation coefficients should be non-negative
        assert var_cont.variation_coefficient >= 0
        assert var_nc.variation_coefficient >= 0
        assert var_all.variation_coefficient >= 0
        assert cons_all.variation_coefficient >= 0
        assert cons_cont.variation_coefficient >= 0
        assert cons_nc.variation_coefficient >= 0

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))

        # All variables have degree 2
        assert var_cont.mean == 2.0
        assert var_cont.median == 2.0

        # No variation
        assert var_cont.variation_coefficient == 0.0

        # All quantiles should be the same
        assert var_cont.q10 == 2.0
        assert var_cont.q90 == 2.0

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))

        # Degrees: x=2, y=2, z=0
        # Mean = (2 + 2 + 0) / 3 = 4/3
        assert var_cont.mean == pytest.approx(4 / 3)

        # Median of [0, 2, 2] = 2
        assert var_cont.median == pytest.approx(2.0)

    def test_single_variable_single_constraint(self) -> None:
        """Test edge case with single variable and single constraint."""
        model = Model("single_single")

        with model.environment:
            x = Variable("x", vtype=Vtype.Real, bounds=Bounds(0, Unbounded))

        model.objective += x
        model.constraints += x <= 10

        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(model)

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        cons_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.CONTINUOUS))

        # Single variable with degree 1
        assert var_cont.mean == 1.0
        assert var_cont.median == 1.0

        # Single constraint with degree 1
        assert cons_cont.mean == 1.0
        assert cons_cont.median == 1.0

        # No variation
        assert var_cont.variation_coefficient == 0.0
        assert cons_cont.variation_coefficient == 0.0

    def test_quadratic_constraints_linear_only(self, quadratic_model: Model) -> None:
        """Test that only linear constraints are considered for graph."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(quadratic_model)

        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # Should only consider linear constraints, not quadratic
        assert var_all.mean >= 0
        assert cons_all.mean >= 0

    def test_all_statistics_non_negative(self, mixed_integer_model: Model) -> None:
        """Test that all statistics are non-negative."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        var_nc = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.NON_CONTINUOUS))
        var_all = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.ALL))
        cons_all = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.ALL))

        # All means should be non-negative
        assert var_cont.mean >= 0
        assert var_nc.mean >= 0
        assert var_all.mean >= 0
        assert cons_all.mean >= 0

        # All medians should be non-negative
        assert var_cont.median >= 0
        assert var_nc.median >= 0
        assert var_all.median >= 0
        assert cons_all.median >= 0

        # All variation coefficients should be non-negative
        assert var_cont.variation_coefficient >= 0
        assert var_nc.variation_coefficient >= 0
        assert var_all.variation_coefficient >= 0
        assert cons_all.variation_coefficient >= 0

        # All quantiles should be non-negative
        assert var_cont.q10 >= 0
        assert var_cont.q90 >= 0
        assert cons_all.q10 >= 0
        assert cons_all.q90 >= 0

    def test_deterministic_results(self, mixed_integer_model: Model) -> None:
        """Test that multiple runs produce identical results."""
        extractor = VariableConstraintGraphFeatures()
        result1 = extractor.run(mixed_integer_model)
        result2 = extractor.run(mixed_integer_model)

        # Check all stats match
        for key in result1.stats:
            assert result1.stats[key].mean == result2.stats[key].mean
            assert result1.stats[key].median == result2.stats[key].median
            assert result1.stats[key].variation_coefficient == result2.stats[key].variation_coefficient

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        cons_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=VarScope.CONTINUOUS))

        # Variable degrees: x1=1, x2=2, x3=1
        # Expect 4/3
        assert var_cont.mean == pytest.approx(4 / 3)

        # Constraint degrees: c1=2, c2=2
        # Expect 2
        assert cons_cont.mean == pytest.approx(2.0)

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

        var_cont = result.get(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS))

        # High variation should result in high VC
        assert var_cont.variation_coefficient > 0.5

    def test_all_values_finite(self, mixed_integer_model: Model) -> None:
        """Test that all returned values are finite."""
        extractor = VariableConstraintGraphFeatures()
        result = extractor.run(mixed_integer_model)

        # Check all stats values are finite
        for key, stats in result.stats.items():
            assert np.isfinite(stats.mean), f"Key {key} mean is not finite: {stats.mean}"
            assert np.isfinite(stats.median), f"Key {key} median is not finite: {stats.median}"
            assert np.isfinite(stats.variation_coefficient), f"Key {key} vc is not finite"
