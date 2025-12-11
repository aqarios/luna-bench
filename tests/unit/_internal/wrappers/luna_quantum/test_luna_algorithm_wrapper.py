from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from luna_quantum import algorithms as lq_algorithms_module
from luna_quantum.solve.domain.abstract.luna_algorithm import (
    LunaAlgorithm as LunaQuantumAlgorithm,
)
from luna_quantum.solve.parameters.algorithms import QAOA
from returns.pipeline import is_successful
from returns.result import Failure, Success

import luna_bench
from luna_bench._internal.interfaces import AlgorithmAsync
from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench._internal.wrappers.luna_quantum.algorithms.luna_algorithm import LunaAlgorithm as BenchLunaAlgorithm
from luna_bench._internal.wrappers.luna_quantum.algorithms.luna_algorithm import LunaData
from luna_bench._internal.wrappers.luna_quantum.luna_algorithm_wrapper import (
    LunaAlgorithmWrapper,
)
from luna_bench.errors.bench_type_errors.algorithm_sub_type_error import AlgorithmSubTypeError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pydantic import BaseModel

    from luna_bench._internal.domain_models import RegisteredDataDomain
    from luna_bench._internal.registries.protocols import PydanticRegistry


def _exported_luna_quantum_algorithm_classes() -> list[type[LunaQuantumAlgorithm[Any]]]:
    exported_names: Iterable[str] | None = getattr(lq_algorithms_module, "__all__", None)
    assert exported_names is not None, "luna_quantum algorithms module must have __all__ attribute"
    classes: list[type[LunaQuantumAlgorithm[Any]]] = []
    for name in exported_names:
        obj: object = getattr(lq_algorithms_module, name)
        if inspect.isclass(obj) and issubclass(obj, LunaQuantumAlgorithm):
            classes.append(obj)
    return classes


@pytest.fixture(scope="module", autouse=True)
def ensure_wrapped() -> None:
    LunaAlgorithmWrapper.wrap_all_algorithms()


@pytest.fixture(scope="module")
def algorithm_registry() -> PydanticRegistry[AlgorithmAsync[Any], RegisteredDataDomain]:
    from luna_bench import _registry_container

    return _registry_container.algorithm_async_registry()


class TestLunaAlgorithmWrapper:
    @pytest.mark.parametrize("cls", _exported_luna_quantum_algorithm_classes())
    def test_get_id_format_for_all_algorithms(self, cls: type[LunaQuantumAlgorithm[Any]]) -> None:
        fake_module: str = LunaAlgorithmWrapper._get_fake_module_name()
        expected_id: str = f"{fake_module}.{cls.__name__}"
        assert LunaAlgorithmWrapper._get_id(cls) == expected_id

    @pytest.mark.parametrize("luna_quantum_algorithm", _exported_luna_quantum_algorithm_classes())
    def test_wrapped_algorithms(
        self,
        algorithm_registry: PydanticRegistry[AlgorithmAsync[BaseModel], Any],
        luna_quantum_algorithm: type[LunaQuantumAlgorithm[Any]],
    ) -> None:
        algo_id = LunaAlgorithmWrapper._get_id(luna_quantum_algorithm)

        assert algorithm_registry.contains(algo_id), f"Missing registration for {algo_id}"

        cls_result = algorithm_registry.get_by_id(algo_id)
        assert is_successful(cls_result), f"Failed to retrieve class for {algo_id}"

        cls = cls_result.unwrap()
        assert cls is not None, f"Failed to retrieve class for {algo_id}"
        assert issubclass(cls, LunaQuantumAlgorithm), f"Class {cls.__name__} is not a subclass of LunaQuantumAlgorithm"
        assert issubclass(cls, BenchLunaAlgorithm), f"Class {cls.__name__} is not a subclass of BenchLunaAlgorithm"
        assert issubclass(cls, AlgorithmAsync), f"Class {cls.__name__} is not a subclass of AlgorithmAsync"

        assert hasattr(cls, "run_async")
        assert hasattr(cls, "fetch_result")

        assert cls.model_type.fget(None) is LunaData

    def test_all_algorithm_added(self) -> None:
        registry = ArbitraryDataRegistry[AlgorithmAsync[Any]](kind="algorithm_async")
        with luna_bench._registry_container.algorithm_async_registry.override(registry):
            LunaAlgorithmWrapper.wrap_all_algorithms()
            assert len(registry.ids()) == len(_exported_luna_quantum_algorithm_classes())

    def test_register_algorithm_manually(self) -> None:
        registry = ArbitraryDataRegistry[AlgorithmAsync[Any]](kind="algorithm_async")
        with luna_bench._registry_container.algorithm_async_registry.override(registry):
            LunaAlgorithmWrapper.register_luna_quantum_algorithm(algorithm_cls=QAOA)
            assert len(registry.ids()) == 1

            LunaAlgorithmWrapper.register_luna_quantum_algorithm(algorithm_cls=object)  # type: ignore[arg-type] # we intentionally pass an invalid type here
            assert len(registry.ids()) == 1

    def test_backend_round_trip_persists_values(
        self, algorithm_registry: PydanticRegistry[AlgorithmAsync[BaseModel], Any]
    ) -> None:
        from luna_quantum.solve.parameters.algorithms import QAOA
        from luna_quantum.solve.parameters.backends import AWS

        device_name = "TN1"
        reps = 1203

        quantum_backend = AWS(device=device_name)  # type: ignore[arg-type] # Inteniontally passing var here so the name is defined on only one place for that test.
        quantum_algorithm: LunaQuantumAlgorithm[Any] = QAOA(reps=reps, backend=quantum_backend)

        assert quantum_algorithm.backend is not None

        bench_algorithm = LunaAlgorithmWrapper.wrap(quantum_algorithm)
        assert isinstance(bench_algorithm, BenchLunaAlgorithm)
        assert bench_algorithm.backend is not None
        assert getattr(bench_algorithm.backend, "device", None) == device_name, (
            f"Backend device should be '{device_name}'"
        )
        assert getattr(bench_algorithm, "reps", None) == reps, f"Algorithm reps should be '{reps}'"

        data = bench_algorithm.model_dump()

        assert isinstance(data, dict)
        assert "backend" in data
        assert isinstance(data["backend"], dict)
        assert data["backend"].get("backend_class_name") == AWS.__name__
        assert data["backend"].get("backend_data", {}).get("device") == device_name

        algorithm_id = LunaAlgorithmWrapper._get_id(QAOA)
        registered_cls = algorithm_registry.get_by_id(algorithm_id).unwrap()
        rebuilt = registered_cls.model_validate(data, from_attributes=True)

        assert rebuilt is not None
        rebuild_backend = getattr(rebuilt, "backend", None)
        assert rebuild_backend is not None
        assert isinstance(rebuild_backend, AWS)
        assert rebuild_backend.device == device_name
        assert getattr(rebuilt, "reps", None) == reps

    def test_wrap_errors(self, algorithm_registry: PydanticRegistry[AlgorithmAsync[BaseModel], Any]) -> None:
        with patch.object(algorithm_registry, "get_by_id") as mock:
            mock.return_value = Failure(UnknownIdError("name", "id"))
            with pytest.raises(UnknownIdError):
                LunaAlgorithmWrapper.wrap(QAOA())

            mock.return_value = Success(QAOA)
            with pytest.raises(AlgorithmSubTypeError):
                LunaAlgorithmWrapper.wrap(QAOA())
