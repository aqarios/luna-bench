import inspect
import sys
from typing import Any

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from luna_quantum.solve.domain.abstract.luna_algorithm import LunaAlgorithm as LunaQuantumAlgorithm
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.parameters import algorithms as algos_module
from pydantic import BaseModel
from returns.pipeline import is_successful

from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.wrappers.luna_quantum import algorithms
from luna_bench._internal.wrappers.luna_quantum.algorithms import LunaAlgorithm
from luna_bench.base_components import BaseAlgorithmAsync
from luna_bench.errors.bench_type_errors.algorithm_sub_type_error import AlgorithmSubTypeError
from luna_bench.helpers.decorators import algorithm


class LunaAlgorithmWrapper:
    _logger = Logging.get_logger(__name__)

    @staticmethod
    def _get_fake_module_name() -> str:
        return f"{algorithms.__package__}"

    @staticmethod
    def _get_id(algorithm_cls: type[IAlgorithm[Any]]) -> str:
        return f"{LunaAlgorithmWrapper._get_fake_module_name()}.{algorithm_cls.__name__}"

    @staticmethod
    def _add_luna_quantum_algorithms() -> None:
        exported_names = getattr(algos_module, "__all__", None)

        if exported_names is None:  # pragma: no cover # We cant really test this since the __all__ attribute is set.
            LunaAlgorithmWrapper._logger.warning(
                "No algorithms found in luna-quantum. Therefore no luna-quantum algorithms will be registered."
            )
            return

        classes: list[type[IAlgorithm[Any]]] = []
        for name in exported_names:
            obj = getattr(algos_module, name)
            if inspect.isclass(obj):
                classes.append(obj)

        for cls in classes:
            if issubclass(cls, LunaQuantumAlgorithm):
                LunaAlgorithmWrapper.register_luna_quantum_algorithm(algorithm_cls=cls)

    @staticmethod
    def wrap_all_algorithms() -> None:
        LunaAlgorithmWrapper._add_luna_quantum_algorithms()

    @staticmethod
    def register_luna_quantum_algorithm(algorithm_cls: type[LunaQuantumAlgorithm[Any]]) -> None:
        if issubclass(algorithm_cls, LunaQuantumAlgorithm):
            target_module_name = LunaAlgorithmWrapper._get_fake_module_name()
            mod = sys.modules.get(target_module_name)

            dyn = type(algorithm_cls.__name__, (LunaAlgorithm, algorithm_cls), {})

            dyn.__module__ = target_module_name
            setattr(mod, dyn.__name__, dyn)

            algorithm(_cls=dyn, algorithm_id=LunaAlgorithmWrapper._get_id(algorithm_cls))
        else:
            LunaAlgorithmWrapper._logger.warning(
                f"Class {algorithm_cls.__name__} is not a subclass of "
                f"{LunaQuantumAlgorithm.__name__} from luna-quantum."
            )

    @staticmethod
    @inject
    def wrap(
        algorithm: IAlgorithm[Any],
        registry: PydanticRegistry[BaseAlgorithmAsync[BaseModel], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
    ) -> LunaAlgorithm:
        result = registry.get_by_id(LunaAlgorithmWrapper._get_id(algorithm.__class__))
        if not is_successful(result):
            raise result.failure()
        cls: type[BaseAlgorithmAsync[Any]] = result.unwrap()

        if not issubclass(cls, LunaAlgorithm):
            raise AlgorithmSubTypeError("LunaAlgorithm")

        x = cls.model_construct(**algorithm.model_dump())

        if isinstance(algorithm, LunaQuantumAlgorithm):
            x.backend = algorithm.backend

        return x
