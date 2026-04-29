from typing import TYPE_CHECKING, ClassVar

import pytest
from luna_model import Model

from luna_bench.base_components.base_feature import BaseFeature
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.errors.components.features.feature_result_unknown_name_error import FeatureResulUnknownNameError
from luna_bench.errors.components.features.feature_result_wrong_class_error import FeatureResultWrongClassError
from luna_bench.types import FeatureClass, FeatureName, FeatureResult

if TYPE_CHECKING:
    from collections.abc import Mapping


class MockFeature(BaseFeature):
    registered_id: ClassVar[str] = "mock_feature"

    def run(self, _model: Model) -> FeatureResult:
        return FeatureResult()


class MockFeature2(BaseFeature):
    registered_id: ClassVar[str] = "mock_feature_2"

    def run(self, _model: Model) -> FeatureResult:
        return FeatureResult()


class TestFeatureResults:
    def test_feature_results_init(self) -> None:
        f1 = MockFeature()
        fr = FeatureResult()
        data: Mapping[FeatureClass, Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]] = {
            MockFeature: {"feat1": (fr, f1)}
        }
        results = FeatureResults.model_construct(allowed=[MockFeature], data=data)
        assert results.allowed == [MockFeature]
        assert results.data == data

    def test_get_all_success(self) -> None:
        f1 = MockFeature()
        fr = FeatureResult()
        data: Mapping[FeatureClass, Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]] = {
            MockFeature: {"feat1": (fr, f1)}
        }
        results = FeatureResults.model_construct(allowed=[MockFeature], data=data)
        assert results.get_all(MockFeature) == {"feat1": fr}
        assert results.get_all_with_config(MockFeature) == {"feat1": (fr, f1)}

    def test_get_all_empty(self) -> None:
        results = FeatureResults.model_construct(allowed=[MockFeature], data={})
        assert results.get_all(MockFeature) == {}

    def test_get_all_wrong_class(self) -> None:
        results = FeatureResults.model_construct(allowed=[MockFeature], data={})
        with pytest.raises(FeatureResultWrongClassError):
            results.get_all(MockFeature2)

    def test_get_success(self) -> None:
        f1 = MockFeature()
        fr = FeatureResult()
        data: Mapping[FeatureClass, Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]] = {
            MockFeature: {"feat1": (fr, f1)}
        }
        results = FeatureResults.model_construct(allowed=[MockFeature], data=data)
        assert results.get(MockFeature, "feat1") == fr
        assert results.get_with_config(MockFeature, "feat1") == (fr, f1)

    def test_get_wrong_class(self) -> None:
        results = FeatureResults.model_construct(allowed=[MockFeature], data={})
        with pytest.raises(FeatureResultWrongClassError):
            results.get(MockFeature2, "feat1")

    def test_get_unknown_name(self) -> None:
        f1 = MockFeature()
        fr = FeatureResult()
        data: Mapping[FeatureClass, Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]] = {
            MockFeature: {"feat1": (fr, f1)}
        }
        results = FeatureResults.model_construct(allowed=[MockFeature], data=data)
        with pytest.raises(FeatureResulUnknownNameError):
            results.get(MockFeature, "feat2")

    def test_first(self) -> None:
        f1 = MockFeature()
        fr = FeatureResult()
        data: Mapping[FeatureClass, Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]] = {
            MockFeature: {"feat1": (fr, f1)}
        }
        results = FeatureResults.model_construct(allowed=[MockFeature], data=data)
        assert results.first(MockFeature) == fr
        assert results.first_with_config(MockFeature) == (fr, f1)
