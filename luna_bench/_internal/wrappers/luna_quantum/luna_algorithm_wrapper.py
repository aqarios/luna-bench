import inspect
import sys
import types
from typing import Any

from dependency_injector.wiring import Provide, inject
from luna_quantum import algorithms as algos_module
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from pydantic import BaseModel
from returns.pipeline import is_successful

from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.interfaces import AlgorithmAsync
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.wrappers.luna_quantum import algorithms
from luna_bench._internal.wrappers.luna_quantum.algorithms import LunaAlgorithm
from luna_bench.errors.bench_type_errors.algorithm_sub_type_error import AlgorithmSubTypeError
from luna_bench.helpers.decorators import algorithm


class LunaAlgorithmWrapper:
    @staticmethod
    def _get_fake_module_name() -> str:
        return f"{algorithms.__package__}"

    @staticmethod
    def _get_id(algorithm_cls: type[IAlgorithm[Any]]) -> str:
        return f"{LunaAlgorithmWrapper._get_fake_module_name()}.{algorithm_cls.__name__}"

    @staticmethod
    def _add_luna_quantum_algorithms() -> None:
        exported_names = getattr(algos_module, "__all__", None)
        if exported_names is None:
            exported_names = [n for n in dir(algos_module) if not n.startswith("_")]

        classes: list[type[IAlgorithm[Any]]] = []
        for name in exported_names:
            obj = getattr(algos_module, name)
            if inspect.isclass(obj):
                classes.append(obj)

        # Ensure the target module exists and is importable
        target_module_name = LunaAlgorithmWrapper._get_fake_module_name()
        mod = sys.modules.get(target_module_name)
        if mod is None:
            mod = types.ModuleType(target_module_name)
            # best-effort metadata
            mod.__file__ = f"<dynamic:{target_module_name}>"
            pkg = target_module_name.rpartition(".")[0]
            mod.__package__ = pkg
            sys.modules[target_module_name] = mod

        for cls in classes:
            # Create dynamic subclass
            dyn = type(cls.__name__, (LunaAlgorithm, cls), {})

            # Point the class at the target module and bind it by its public name
            dyn.__module__ = target_module_name
            setattr(mod, dyn.__name__, dyn)

            # Register with your decorator using the same module-qualified id
            algorithm(_cls=dyn, algorithm_id=LunaAlgorithmWrapper._get_id(cls))

    @staticmethod
    def wrap_algorithms() -> None:
        LunaAlgorithmWrapper._add_luna_quantum_algorithms()

    @staticmethod
    @inject
    def wrap(
        algorithm: IAlgorithm[Any],
        registry: PydanticRegistry[AlgorithmAsync[BaseModel], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
    ) -> LunaAlgorithm:
        result = registry.get_by_id(LunaAlgorithmWrapper._get_id(algorithm.__class__))
        if not is_successful(result):
            raise result.failure()
        cls: type[AlgorithmAsync[Any]] = result.unwrap()

        if not issubclass(cls, LunaAlgorithm):
            raise AlgorithmSubTypeError("LunaAlgorithm")

        return cls.model_construct(**algorithm.model_dump())
