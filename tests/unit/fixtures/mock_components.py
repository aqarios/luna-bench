from luna_quantum import Model, Solution

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import AlgorithmSync
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench.helpers.decorators import algorithm, feature, metric, plot


@feature
class MockFeature(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        return ArbitraryDataDomain.model_construct(solution="xD")  # type: ignore[call-arg] # Fake data


@feature
class MockFeatureFailing(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        raise ValueError("Model failed.")  # noqa: TRY003 # Just simulating a random error


class UnregisteredFeature(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:
        raise NotImplementedError


@algorithm
class MockAlgorithm(AlgorithmSync):
    def run(self, model: Model) -> Solution:
        raise NotImplementedError


class UnregisteredAlgorithm(AlgorithmSync):
    def run(self, model: Model) -> Solution:
        raise NotImplementedError


@plot
class MockPlot(IPlot):
    def run(self) -> None:
        raise NotImplementedError


class UnregisteredPlot(IPlot):
    def run(self) -> None:
        raise NotImplementedError


@metric
class MockMetric(IMetric):
    def run(self) -> None:
        raise NotImplementedError


class UnregisteredMetric(IMetric):
    def run(self) -> None:
        raise NotImplementedError
