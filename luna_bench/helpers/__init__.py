from . import decorators
from .decorators import algorithm, algorithms, feature, features, metric, metrics, plot, plots, registry_info

__all__ = [
    "algorithm",
    "algorithms",
    "feature",
    "features",
    "metric",
    "metrics",
    "plot",
    "plots",
    "registry_info",
]

from luna_bench._internal.registries.registry_container import registry_container

registry_container.wire(modules=[decorators])
