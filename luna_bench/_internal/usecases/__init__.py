from luna_bench._internal.async_tasks import huey_algorithm_runner
from luna_bench._internal.dao.dao_container import DaoContainer
from luna_bench._internal.mappers.container import MapperContainer
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

_mapper_container = MapperContainer()

_dao_container.wire(modules=[modelset, benchmark, huey_algorithm_runner])
from luna_bench._internal.wrappers.luna_quantum import luna_algorithm_wrapper

registry_container.wire(modules=[modelset, benchmark, "luna_bench.helpers", luna_algorithm_wrapper])
_mapper_container.wire(modules=[modelset, benchmark])


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
