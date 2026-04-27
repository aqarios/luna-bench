from typing import TYPE_CHECKING

from luna_bench.base_components.data_types.arbitrary_data import ArbitraryData


class FeatureResult(ArbitraryData):
    """Specific container for feature results."""


class MetricResult(ArbitraryData):
    """Specific container for metric results."""


if TYPE_CHECKING:
    from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
    from luna_bench.base_components.base_feature import BaseFeature
    from luna_bench.base_components.base_metric import BaseMetric

    type FeatureClass[TFeatureResult: ArbitraryDataDomain = ArbitraryDataDomain] = type["BaseFeature[TFeatureResult]"]
    type MetricClass[TMetricResult: MetricResult = MetricResult] = type["BaseMetric[TMetricResult]"]
else:
    BaseFeature = None
    BaseMetric = None
    type FeatureClass = type["BaseFeature"]
    type MetricClass = type["BaseMetric"]

type AlgorithmName = str
type BenchmarkName = str
type ModelName = str
type FeatureName = str
type MetricName = str
type PlotName = str
type ModelSetName = str

type FeatureComputed = tuple["FeatureResult", "BaseFeature"]
type MetricComputed = tuple["MetricResult", "BaseMetric"]
