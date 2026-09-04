"""Tests for registering a whole grid of algorithm variants in one call."""

from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, ValidationError
from returns.result import Success

from luna_bench import Benchmark
from luna_bench.algorithms.variants import AlgorithmGrid, ParameterGrid
from luna_bench.custom import BaseAlgorithmSync
from luna_bench.entities import AlgorithmEntity, BenchmarkEntity
from luna_bench.errors.components.algorithms.unknown_parameter_path_error import UnknownParameterPathError
from tests.unit.fixtures.mock_components import MockAlgorithm

if TYPE_CHECKING:
    from collections.abc import Generator

    from luna_model import Model, Solution


class Pipeline(BaseModel):
    """Nested configuration, standing in for FlexQAOA's pipeline."""

    enable: bool = True


class Algo(BaseAlgorithmSync):
    """Algorithm-shaped model, varied by the tests below."""

    reps: int = 1
    pipeline: Pipeline = Pipeline()

    def run(self, model: Model) -> Solution:
        raise NotImplementedError


class TestAddAlgorithmWithVariants:
    @pytest.fixture(autouse=True)
    def mocked_usecases(self) -> Generator[dict[str, MagicMock]]:
        from luna_bench import _usecase_container

        mocks = {}
        with ExitStack() as stack:
            for name, provider in _usecase_container.providers.items():
                if name.endswith("_uc"):
                    mock = MagicMock(name=name)
                    stack.enter_context(provider.override(mock))
                    mocks[name] = mock
            yield mocks

    @pytest.fixture()
    def bench(self) -> Benchmark:
        return Benchmark.model_construct(
            **BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[]).model_dump()
        )

    @pytest.fixture(autouse=True)
    def registers(self, mocked_usecases: dict[str, MagicMock]) -> MagicMock:
        """Make the add-algorithm usecase echo back an entity per call."""
        mock = mocked_usecases["benchmark_add_algorithm_uc"]
        mock.side_effect = lambda _b, name, _a: Success(
            AlgorithmEntity(name=name, algorithm=MockAlgorithm(), results={})
        )
        return mock

    def test_registers_one_entry_per_variant(self, bench: Benchmark, registers: MagicMock) -> None:
        grid = bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"reps": [2, 4, 6]}))

        assert len(grid.entities) == 3
        assert registers.call_count == 3

    def test_returns_an_algorithm_grid(self, bench: Benchmark) -> None:
        grid = bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"reps": [2, 4]}))

        assert isinstance(grid, AlgorithmGrid)

    def test_names_each_entry_after_the_parameters_that_made_it(self, bench: Benchmark) -> None:
        grid = bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"reps": [2, 4]}))

        assert [entity.name for entity in grid.entities] == ["algo[reps=2]", "algo[reps=4]"]

    def test_names_keep_the_full_dotted_path_so_two_axes_cannot_collide(self, bench: Benchmark) -> None:
        grid = bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"pipeline.enable": [False]}))

        assert grid.entities[0].name == "algo[pipeline.enable=False]"

    def test_each_registered_algorithm_carries_its_own_parameters(self, bench: Benchmark, registers: MagicMock) -> None:
        bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"reps": [2, 6]}))

        registered = [call.args[2].reps for call in registers.call_args_list]
        assert registered == [2, 6]

    def test_the_axes_map_every_entry_to_its_value(self, bench: Benchmark) -> None:
        grid = bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"reps": [2, 4]}))

        assert grid.axes == {"reps": {"algo[reps=2]": 2, "algo[reps=4]": 4}}

    def test_a_bare_list_of_configurations_is_accepted(self, bench: Benchmark) -> None:
        grid = bench.add_algorithm("algo", Algo(), variants=[{"reps": 2}, {"reps": 6}])

        assert [entity.name for entity in grid.entities] == ["algo[reps=2]", "algo[reps=6]"]

    def test_an_unknown_path_registers_nothing_at_all(self, bench: Benchmark, registers: MagicMock) -> None:
        with pytest.raises(UnknownParameterPathError):
            bench.add_algorithm("algo", Algo(), variants=ParameterGrid({"repetitions": [2, 4]}))

        assert registers.call_count == 0
        assert bench.algorithms == []

    def test_a_value_of_the_wrong_type_registers_nothing_at_all(self, bench: Benchmark, registers: MagicMock) -> None:
        with pytest.raises(ValidationError):
            bench.add_algorithm("algo", Algo(), variants=[{"reps": "many"}])

        assert registers.call_count == 0

    def test_without_variants_a_single_entity_is_still_returned(self, bench: Benchmark) -> None:
        result = bench.add_algorithm("algo", MagicMock())

        assert isinstance(result, AlgorithmEntity)
