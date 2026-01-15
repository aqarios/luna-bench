from luna_bench.base_components.data_types.arbitrary_data import ArbitraryData

type AlgorithmName = str
type BenchmarkName = str
type ModelName = str
type FeatureName = str
type MetricName = str
type PlotName = str
type ModelSetName = str


class FeatureResult(ArbitraryData):
    """Specific container for feature results."""


class MetricResult(ArbitraryData):
    """Specific container for metric results."""
