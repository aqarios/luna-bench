from typing import Any

from luna_quantum import Model
from luna_quantum.solve import SolveJob
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench.helpers.decorators import algorithm, feature, metric, plot


@feature
class MockFeature(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:
        raise NotImplementedError


class UnregisteredFeature(IFeature):
    def run(self, model: Model) -> ArbitraryDataDomain:
        raise NotImplementedError


@algorithm
class MockAlgorithm(IAlgorithm[IBackend]):
    def run(
        self,
        model: Model | str,
        name: str | None = None,
        backend: IBackend | None = None,
        *args: Any | None,
        **kwargs: Any | None,
    ) -> SolveJob:
        raise NotImplementedError


class UnregisteredAlgorithm(IAlgorithm[IBackend]):
    def run(
        self,
        model: Model | str,
        name: str | None = None,
        backend: IBackend | None = None,
        *args: Any | None,
        **kwargs: Any | None,
    ) -> SolveJob:
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
