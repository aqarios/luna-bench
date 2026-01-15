from unittest.mock import Mock

from returns.pipeline import is_successful
from returns.result import Failure, Success

from luna_bench._internal.usecases.benchmark import AlgorithmRunUcImpl
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmFilterUc,
    AlgorithmRetrieveAsyncRetrivalDataUc,
    AlgorithmRetrieveAsyncSolutionsUc,
    AlgorithmRetrieveSyncSolutionsUc,
    AlgorithmRunAsBackgroundTasksUc,
)
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.entities.model_set_entity import ModelSetEntity
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError


class TestAlgorithmRunUc:
    def setup_method(self) -> None:
        self.mock_filter = Mock(spec=AlgorithmFilterUc)
        self.mock_start_tasks = Mock(spec=AlgorithmRunAsBackgroundTasksUc)
        self.mock_retrieve_sync = Mock(spec=AlgorithmRetrieveSyncSolutionsUc)
        self.mock_retrieve_async_retrieval_data = Mock(spec=AlgorithmRetrieveAsyncRetrivalDataUc)
        self.mock_retrieve_async_solution_data = Mock(spec=AlgorithmRetrieveAsyncSolutionsUc)

        self.uc = AlgorithmRunUcImpl(
            algorithm_filter=self.mock_filter,
            start_tasks=self.mock_start_tasks,
            retrieve_sync=self.mock_retrieve_sync,
            retrieve_async_retrieval_data=self.mock_retrieve_async_retrieval_data,
            retrieve_async_solution_data=self.mock_retrieve_async_solution_data,
        )

    def test_algorithm_without_modelset_run(self) -> None:
        result = self.uc(
            BenchmarkEntity(
                name="test",
                modelset=None,
                features=[],
                algorithms=[],
                metrics=[],
                plots=[],
            )
        )
        assert not is_successful(result)
        assert isinstance(result.failure(), type(RunModelsetMissingError("test")))

        assert self.mock_filter.call_count == 2
        self.mock_retrieve_sync.assert_not_called()
        self.mock_retrieve_async_retrieval_data.assert_not_called()
        self.mock_retrieve_async_solution_data.assert_not_called()
        self.mock_start_tasks.assert_not_called()

    def test_algorithm_modelset_run(self) -> None:
        result = self.uc(
            BenchmarkEntity(
                name="test",
                modelset=ModelSetEntity(id=0, name="test", models=[]),
                features=[],
                algorithms=[],
                metrics=[],
                plots=[],
            )
        )
        assert is_successful(result)

        assert self.mock_filter.call_count == 2
        self.mock_retrieve_sync.assert_called_once()
        self.mock_retrieve_async_retrieval_data.assert_called_once()
        self.mock_retrieve_async_solution_data.assert_called_once()
        assert self.mock_start_tasks.call_count == 2  # On time for sync and one for async

    def test_algorithm_filter_failures_first(self) -> None:
        self.mock_filter.side_effect = [Failure(RunAlgorithmMissingError("mock", "mock")), Success(None)]
        result = self.uc(
            BenchmarkEntity(
                name="test",
                modelset=None,
                features=[],
                algorithms=[],
                metrics=[],
                plots=[],
            )
        )
        assert not is_successful(result)
        assert isinstance(result.failure(), type(RunAlgorithmMissingError("mock", "mock")))

        assert self.mock_filter.call_count == 2
        self.mock_retrieve_sync.assert_not_called()
        self.mock_retrieve_async_retrieval_data.assert_not_called()
        self.mock_retrieve_async_solution_data.assert_not_called()
        self.mock_start_tasks.assert_not_called()

    def test_algorithm_filter_failures_second(self) -> None:
        self.mock_filter.side_effect = [Success(None), Failure(RunAlgorithmMissingError("mock", "mock"))]
        result = self.uc(
            BenchmarkEntity(
                name="test",
                modelset=None,
                features=[],
                algorithms=[],
                metrics=[],
                plots=[],
            )
        )
        assert not is_successful(result)
        assert isinstance(result.failure(), type(RunAlgorithmMissingError("mock", "mock")))

        assert self.mock_filter.call_count == 2
        self.mock_retrieve_sync.assert_not_called()
        self.mock_retrieve_async_retrieval_data.assert_not_called()
        self.mock_retrieve_async_solution_data.assert_not_called()
        self.mock_start_tasks.assert_not_called()
