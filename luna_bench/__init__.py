from luna_bench._internal.usecases import UsecaseContainer
from luna_bench.configs.config import config

_container = UsecaseContainer()
_container.config.from_pydantic(config)
_container.wire(
    modules=[
        "luna_bench.components",
    ]
)
