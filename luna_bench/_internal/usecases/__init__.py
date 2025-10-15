from luna_bench._internal.dao.dao_container import DaoContainer
from luna_bench._internal.registries.registry_container import registry_container
from luna_bench.configs.config import config

from . import benchmark, modelset
from .benchmark.protocols import (
    AlgorithmAddUc,
    AlgorithmRemoveUc,
    BenchmarkCreateUc,
    BenchmarkDeleteUc,
    BenchmarkLoadAllUc,
    BenchmarkLoadUc,
    BenchmarkRemoveModelsetUc,
    BenchmarkSetModelsetUc,
    FeatureAddUc,
    FeatureRemoveUc,
    MetricAddUc,
    MetricRemoveUc,
    PlotAddUc,
    PlotRemoveUc,
)
from .modelset.protocols import (
    ModelAddUc,
    ModelFetchUc,
    ModelLoadAllUc,
    ModelRemoveUc,
    ModelSetCreateUc,
    ModelSetDeleteUc,
    ModelSetLoadAllUc,
    ModelSetLoadUc,
)
from .usecase_container import UsecaseContainer

_dao_container = DaoContainer()
_dao_container.config.from_pydantic(config)

_dao_container.wire(modules=[modelset, benchmark])
registry_container.wire(modules=[modelset, benchmark])


__all__ = [
    "AlgorithmAddUc",
    "AlgorithmRemoveUc",
    "BenchmarkCreateUc",
    "BenchmarkDeleteUc",
    "BenchmarkLoadAllUc",
    "BenchmarkLoadUc",
    "BenchmarkRemoveModelsetUc",
    "BenchmarkSetModelsetUc",
    "FeatureAddUc",
    "FeatureRemoveUc",
    "MetricAddUc",
    "MetricRemoveUc",
    "ModelAddUc",
    "ModelFetchUc",
    "ModelLoadAllUc",
    "ModelRemoveUc",
    "ModelSetCreateUc",
    "ModelSetDeleteUc",
    "ModelSetLoadAllUc",
    "ModelSetLoadUc",
    "PlotAddUc",
    "PlotRemoveUc",
    "UsecaseContainer",
]
