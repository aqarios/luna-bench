from luna_bench._internal.usecases import UsecaseContainer
from luna_bench.components.algorithms import FakeAlgorithm
from luna_bench.components.features import FakeFeature
from luna_bench.components.metrics import FakeMetric
from luna_bench.components.plots import FakePlot
from luna_bench.configs.config import config

_usecase_container = UsecaseContainer()
_usecase_container.config.from_pydantic(config)
_usecase_container.wire(
    modules=[
        "luna_bench.components",
    ]
)


__all__ = [
    "FakeAlgorithm",
    "FakeFeature",
    "FakeMetric",
    "FakePlot",
]
