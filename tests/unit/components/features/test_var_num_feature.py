from luna_quantum import Model

from luna_bench.components.features.var_num_feature import VarNumberFeature

class TestVarNumberFeature:

    def test_var_number_feature(self, regular_model: Model) -> None:
        """Test feature extraction on a simple linear model."""
        feature = VarNumberFeature()
        result = feature.run(regular_model)
        assert result.var_number == regular_model.num_variables


    def test_empty_model(self) -> None:
        """Test edge case of an emtpy model."""
        empty_model = Model("empty")
        var_num_feature = VarNumberFeature()
        result = var_num_feature.run(empty_model)
        assert result.var_number == 0


    def test_fixed_var_model(self) -> None:
        """Check the case of a fixed variable, which should be still counted towards the variable number."""

        # Generate a model and fix variable x
        fixed_model = Model("fixed_variable")
        with fixed_model.environment:
            x = fixed_model.add_variable("fixed_variable")
        fixed_model.add_constraint(x == 1)

        # execute feature
        var_num_feature = VarNumberFeature()
        result = var_num_feature.run(fixed_model)

        # Check if variable x is counted
        assert result.var_number == 1
