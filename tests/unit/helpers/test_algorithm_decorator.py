import pickle
from typing import cast

import cloudpickle
import pytest
from luna_model import Model, Solution
from pydantic import BaseModel
from returns.result import Result, Success

from luna_bench._internal.registries import Registry
from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.custom import BaseAlgorithmAsync, BaseAlgorithmSync
from luna_bench.custom.decorators.algorithm import _rebuild_algorithm, algorithm
from luna_bench.errors.decorators.invalid_return_type_error import InvalidReturnTypeError
from luna_bench.errors.incompatible_class_error import IncompatibleClassError


class TestAlgorithmSyncDecorator:
    @pytest.fixture()
    def sync_registry(self) -> Registry[BaseAlgorithmSync]:
        return ArbitraryDataRegistry[BaseAlgorithmSync](kind="sync_algo")

    @pytest.mark.parametrize(
        "algorithm_id",
        [
            None,
            "custom.algo_id",
        ],
        ids=["default_id", "custom_id"],
    )
    def test_algorithm_sync_class_registration(
        self,
        algorithm_id: str | None,
    ) -> None:
        @algorithm(algorithm_id=algorithm_id)
        class TestAlgorithm(BaseAlgorithmSync):
            def run(self, model: Model) -> Solution:
                _ = model
                return cast("Solution", {})

        assert isinstance(TestAlgorithm, type)
        assert issubclass(TestAlgorithm, BaseAlgorithmSync)

    def test_algorithm_preserves_function_metadata(self) -> None:
        @algorithm
        def documented_algorithm(model: Model) -> Solution:
            """Run, this is the algorithm documentation."""
            _ = model

            return Solution(samples=[])

        assert documented_algorithm.__doc__ == "Run, this is the algorithm documentation."
        assert documented_algorithm.__name__ == "documented_algorithm"

    def test_algorithm_sync_function_registration(self) -> None:
        @algorithm
        def sync_func_algo(model: Model) -> Solution:
            _ = model

            return Solution(samples=[])

        assert isinstance(sync_func_algo, type)
        assert issubclass(sync_func_algo, BaseAlgorithmSync)

    def test_algorithm_sync_function_execution(self) -> None:
        from luna_model import Solution

        @algorithm
        def executable_algo(model: Model) -> Solution:
            _ = model
            return Solution(samples=[])

        algo_inst = executable_algo()
        result = algo_inst.run(cast("Model", {}))
        assert isinstance(result, Solution)

    def test_algorithm_sync_function_invalid_return_type(self) -> None:
        @algorithm  # type: ignore[arg-type]
        def invalid_algo(model: Model) -> str:
            _ = model
            return "not_a_solution"

        algo_inst = invalid_algo()

        with pytest.raises(InvalidReturnTypeError):
            algo_inst.run(cast("Model", {}))

    def test_algorithm_incompatible_class(self) -> None:
        with pytest.raises(IncompatibleClassError):

            @algorithm
            class NotAnAlgorithm:  # type: ignore[type-var]
                pass

    def test_algorithm_sync_function_pickle_roundtrip(self) -> None:

        @algorithm
        def algo_to_pickle(model: Model) -> Solution:
            _ = model
            return Solution(samples=[])

        inst = algo_to_pickle()
        data = pickle.dumps(inst)
        restored = pickle.loads(data)

        assert isinstance(restored, BaseAlgorithmSync)
        assert type(restored).__name__ == "algo_to_pickle"
        assert hasattr(restored, "run")
        result = restored.run(cast("Model", {}))
        assert isinstance(result, Solution)

    def test_algorithm_inline_pickle_roundtrip(self) -> None:
        exec_globals: dict[str, object] = {"__name__": "__main__"}
        exec(
            (
                "from luna_model import Model, Solution\n"
                "from luna_bench.custom.decorators.algorithm import algorithm\n"
                "\n"
                "@algorithm()\n"
                "def main_algo(model: Model) -> Solution:\n"
                "    _ = model\n"
                "    return Solution(samples=[])\n"
            ),
            exec_globals,
        )

        algo_cls = exec_globals["main_algo"]
        assert isinstance(algo_cls, type)
        assert issubclass(algo_cls, BaseAlgorithmSync)

        inst = algo_cls()
        data = pickle.dumps(inst)
        restored = pickle.loads(data)

        assert isinstance(restored, BaseAlgorithmSync)
        assert hasattr(restored, "run")
        result = restored.run(cast("Model", {}))
        assert isinstance(result, Solution)

    def test_rebuild_algorithm_invalid_return_type(self) -> None:
        """Verify that _rebuild_algorithm raises InvalidReturnTypeError.

        The deserialised function returns a non-Solution value.
        """

        def bad_func(_model: Model) -> str:
            return "not_a_solution"

        bad_bytes = cloudpickle.dumps(bad_func)
        restored = _rebuild_algorithm(bad_bytes)

        with pytest.raises(InvalidReturnTypeError):
            restored.run(cast("Model", {}))


class TestAlgorithmAsyncDecorator:
    def test_algorithm_async_class_registration(self) -> None:
        class AsyncState(BaseModel):
            job_id: str

        @algorithm
        class AsyncTestAlgorithm(BaseAlgorithmAsync[AsyncState]):
            @property
            def model_type(self) -> type[AsyncState]:
                return AsyncState

            def run_async(self, model: Model) -> AsyncState:
                _ = model
                return AsyncState(job_id="job_123")

            def fetch_result(self, model: Model, retrieval_data: AsyncState) -> Result[Solution, str]:
                _ = model
                return Success(cast("Solution", {"job_id": retrieval_data.job_id}))

        assert isinstance(AsyncTestAlgorithm, type)
        assert issubclass(AsyncTestAlgorithm, BaseAlgorithmAsync)

    @pytest.mark.parametrize(
        "algorithm_id",
        [
            "custom.async.algo",
        ],
        ids=["custom_id"],
    )
    def test_algorithm_async_with_custom_id(
        self,
        algorithm_id: str | None,
    ) -> None:
        class CustomAsyncState(BaseModel):
            data: str

        @algorithm(algorithm_id=algorithm_id)
        class CustomAsync(BaseAlgorithmAsync[CustomAsyncState]):
            @property
            def model_type(self) -> type[CustomAsyncState]:
                return CustomAsyncState

            def run_async(self, model: Model) -> CustomAsyncState:
                _ = model
                return CustomAsyncState(data="test")

            def fetch_result(self, model: Model, retrieval_data: CustomAsyncState) -> Result[Solution, str]:
                _ = model
                _ = retrieval_data
                return Success(cast("Solution", {}))

        assert isinstance(CustomAsync, type)
        assert issubclass(CustomAsync, BaseAlgorithmAsync)
