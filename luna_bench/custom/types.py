from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from luna_model import Solution

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

#: What an algorithm may hand back. The bare ``Solution`` is the shape every algorithm had
#: before metadata existed and still the right one for a solver with nothing to add; the pair
#: reports what the solver knows about the run itself. ``Solution`` is imported at runtime
#: rather than under ``TYPE_CHECKING`` because this alias appears in the return annotation of
#: user-written algorithms, where it may be resolved.
type SolveOutcome = Solution | tuple[Solution, Mapping[str, Any]]

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
