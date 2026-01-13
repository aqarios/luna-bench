
from luna_bench.components.features.fake_feature import FakeFeature
from luna_quantum import Model

def test_range_fake() -> None:
    f_feature = FakeFeature()
    model_name = 'empty_model'
    empty_model = Model(model_name)
    f_result = f_feature.run(empty_model)
    assert f_result.random_number >= 0 and f_result.random_number <= 100
    assert f_result.fake_feature_model_name == model_name