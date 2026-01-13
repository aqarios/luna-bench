from luna_bench.components.features.mip.problem_size_feature import ModelBoundsError


def test_instantiation() -> None:
    err = ModelBoundsError()
    assert isinstance(err, Exception)
    assert str(err) == ""


def test_with_model_name_only():
    err = ModelBoundsError(model_name="MyModel")
    s = str(err)
    assert "(model: MyModel)" in s
    # no expected_bounds appended
    assert "(expected:" not in s


def test_with_expected_bounds_only():
    err = ModelBoundsError(expected_bounds="[-1, 1]")
    s = str(err)
    assert "(expected: [-1, 1])" in s
    # no model_name appended
    assert "model:" not in s



