from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from luna_bench.custom.base_components.base_feature import BaseFeature
    from luna_bench.custom.base_components.base_metric import BaseMetric
    from luna_bench.custom.base_results.feature_result import FeatureResult
    from luna_bench.custom.base_results.metric_result import MetricResult

    type FeatureClass[TFeatureResult: FeatureResult = FeatureResult] = type[BaseFeature[TFeatureResult]]
    type MetricClass[TMetricResult: MetricResult = MetricResult] = type[BaseMetric[TMetricResult]]
else:
    # Runtime-only fallbacks: keep aliases concrete so Pydantic can resolve them
    # without needing TYPE_CHECKING-only symbols.
    type FeatureClass = type[object]
    type MetricClass = type[object]

type AlgorithmName = str
type BenchmarkName = str
type ModelName = str
type FeatureName = str
type MetricName = str
type PlotName = str
type ModelSetName = str

if TYPE_CHECKING:
    type FeatureComputed = tuple["FeatureResult", "BaseFeature"]
    type MetricComputed = tuple["MetricResult", "BaseMetric"]
else:
    type FeatureComputed = tuple[object, object]
    type MetricComputed = tuple[object, object]
