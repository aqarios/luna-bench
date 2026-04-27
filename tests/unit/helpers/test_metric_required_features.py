from typing import TYPE_CHECKING

import pytest

from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.errors.incompatible_class_error import IncompatibleClassError
from luna_bench.helpers.decorators import metric

if TYPE_CHECKING:
    from luna_model import Model, Solution

    from luna_bench.base_components.data_types.feature_results import FeatureResults
    from luna_bench.types import FeatureResult, MetricResult


class MockFeature(BaseFeature):
    def run(self, model: "Model") -> FeatureResult:
        raise NotImplementedError


class MockMetric(BaseMetric["MetricResult"]):
    def run(
        self,
        solution: "Solution",
        feature_results: "FeatureResults",
    ) -> "MetricResult":
        raise NotImplementedError


class TestMetricRequiredFeatures:
    def test_metric_required_features_none(self) -> None:
        @metric(required_features=None)
        class MetricNone(MockMetric):
            pass

        assert MetricNone.required_features == []

    def test_metric_required_features_single(self) -> None:
        @metric(required_features=MockFeature)
        class MetricSingle(MockMetric):
            pass

        assert MetricSingle.required_features == [MockFeature]

    def test_metric_required_features_list(self) -> None:
        @metric(required_features=[MockFeature])
        class MetricList(MockMetric):
            pass

        assert MetricList.required_features == [MockFeature]

    def test_metric_required_features_tuple(self) -> None:
        @metric(required_features=(MockFeature,))
        class MetricTuple(MockMetric):
            pass

        assert MetricTuple.required_features == [MockFeature]

    def test_metric_incompatible_class(self) -> None:
        with pytest.raises(IncompatibleClassError):

            @metric()
            class NotAMetric:  # type: ignore[type-var]
                pass
