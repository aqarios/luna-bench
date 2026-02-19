from luna_bench._internal.background_tasks.background_task_container import BackgroundTaskContainer
from luna_bench._internal.dao.dao_container import DaoContainer
from luna_bench._internal.mappers.container import MapperContainer
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases import UsecaseContainer
from luna_bench.configs.config import config

_usecase_container = UsecaseContainer()
_registry_container = RegistryContainer()
_mapper_container = MapperContainer()
_dao_container = DaoContainer()
_bg_task_container = BackgroundTaskContainer()

_mapper_container.registry_container.override(_registry_container)
_usecase_container.mapper_container.override(_mapper_container)
_usecase_container.dao_container.override(_dao_container)
_usecase_container.bg_task_container.override(_bg_task_container)

_dao_container.config.from_pydantic(config)
_usecase_container.config.from_pydantic(config)

_registry_container.wire(
    modules=[
        "luna_bench.helpers.decorators",
        "luna_bench.helpers",
        "luna_bench._internal.usecases.modelset",
        "luna_bench._internal.usecases.benchmark",
        "luna_bench.components",
        "luna_bench._internal.wrappers",
    ]
)
_bg_task_container.wire(
    modules=[
        "luna_bench._internal.usecases.background_tasks",
        "luna_bench._internal.usecases.benchmark",
    ]
)

_usecase_container.wire(
    modules=[
        "luna_bench.components",
        "luna_bench.components.plots",
    ]
)

_dao_container.wire(
    modules=[
        "luna_bench._internal.usecases.modelset",
        "luna_bench._internal.usecases.benchmark",
        "luna_bench._internal.background_tasks.huey.huey_algorithm_runner",
    ]
)


_mapper_container.wire(
    modules=[
        "luna_bench._internal.usecases.modelset",
        "luna_bench._internal.usecases.benchmark",
    ]
)

# Import components AFTER wiring to ensure decorators have access to injected registries
from luna_bench.components import Benchmark, ModelSet, ModelMetadata
import luna_bench.components.algorithms as Algorithm  # noqa: E402
import luna_bench.components.features as Feature  # noqa: E402
import luna_bench.components.metrics as Metric  # noqa: E402
import luna_bench.components.plots as Plot  # noqa: E402

__all__ = (
    "Benchmark",
    "ModelSet",
    "ModelMetadata",
    "Algorithm",
    "Feature",
    "Metric",
    "Plot",
)

# Import and wrapping after the wiring is done,
# to ensure the wrappers and decorators have access to the injected registries
from luna_bench._internal.wrappers import LunaAlgorithmWrapper  # noqa: E402

LunaAlgorithmWrapper.wrap_all_algorithms()
