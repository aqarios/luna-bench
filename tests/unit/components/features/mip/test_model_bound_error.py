from luna_bench.features.mip.problem_size_feature import ModelBoundsError


def test_instantiation() -> None:
    err = ModelBoundsError()
    assert isinstance(err, Exception)
    assert str(err) == ""


def test_with_model_name_only() -> None:
    err = ModelBoundsError(model_name="MyModel")
    s = str(err)
    assert "(model: MyModel)" in s
    assert "(expected:" not in s


def test_with_expected_bounds_only() -> None:
    err = ModelBoundsError(expected_bounds="[-1, 1]")
    s = str(err)
    assert "(expected: [-1, 1])" in s
    assert "model:" not in s
