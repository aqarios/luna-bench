from luna_quantum import Model

from luna_bench.components.features.fake_feature import FakeFeature


class TestFakeFeature:
    def test_range_fake(self) -> None:
        """Simple test to check if a random number within the defined range is generated."""
        f_feature = FakeFeature()
        model_name = "empty_model"
        empty_model = Model(model_name)
        f_result = f_feature.run(empty_model)

        # Check that lower bound is valid
        assert f_result.random_number >= 0

        # Check that upper bound is valid
        assert f_result.random_number <= 100

        # Check that model name is correctly passed
        assert f_result.fake_feature_model_name == model_name
