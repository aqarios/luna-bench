from typing import TYPE_CHECKING

from luna_bench.base_components.data_types.arbitrary_data import ArbitraryData

if TYPE_CHECKING:
    from luna_bench.base_components.base_feature import BaseFeature
    from luna_bench.base_components.base_metric import BaseMetric
else:
    BaseFeature = None
    BaseMetric = None

type AlgorithmName = str
type BenchmarkName = str
type ModelName = str
type FeatureName = str
type MetricName = str
type PlotName = str
type ModelSetName = str

type FeatureComputed = tuple["FeatureResult", "BaseFeature"]
type MetricComputed = tuple["MetricResult", "BaseMetric"]

type FeatureClass = type["BaseFeature"]
type MetricClass = type["BaseMetric"]


class FeatureResult(ArbitraryData):
    """Specific container for feature results."""


class MetricResult(ArbitraryData):
    """Specific container for metric results."""
