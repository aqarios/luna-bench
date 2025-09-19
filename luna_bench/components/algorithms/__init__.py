import inspect

from luna_quantum import algorithms as algos_module

from luna_bench.helpers import algorithm

from .fake_algorithm import FakeAlgorithm

__all__ = ["FakeAlgorithm"]


def _add_luna_quantum_algorithms() -> None:
    exported_names = getattr(algos_module, "__all__", None)
    if exported_names is None:
        exported_names = [n for n in dir(algos_module) if not n.startswith("_")]

    classes = []
    for name in exported_names:
        obj = getattr(algos_module, name)
        if inspect.isclass(obj):
            classes.append(obj)

    for cls in classes:
        algorithm(_cls=cls)


_add_luna_quantum_algorithms()
