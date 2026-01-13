from luna_quantum import Model

from luna_bench.components.features.var_num_feature import VarNumberFeature


def test_var_number_feature(regular_model: Model) -> None:
    feature = VarNumberFeature()
    result = feature.run(regular_model)
    assert result.var_number == regular_model.num_variables


def test_empty_model() -> None:
    empty_model = Model("empty")
    var_num_feature = VarNumberFeature()
    result = var_num_feature.run(empty_model)
    assert result.var_number == 0


def test_fixed_var_model() -> None:
    fixed_model = Model("fixed_variable")
    with fixed_model.environment:
        x = fixed_model.add_variable("fixed_variable")
    fixed_model.add_constraint(x == 1)
    var_num_feature = VarNumberFeature()
    result = var_num_feature.run(fixed_model)
    assert result.var_number == 1
