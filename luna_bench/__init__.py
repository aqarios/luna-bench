from luna_bench._internal.di.container import Container

_container = Container()
_container.wire(
    modules=[
        "luna_bench.components",
    ]
)
