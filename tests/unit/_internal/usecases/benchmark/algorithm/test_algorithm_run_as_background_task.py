from unittest.mock import MagicMock

from returns.pipeline import is_successful

from luna_bench import MapperContainer  # type: ignore[attr-defined]
from luna_bench._internal.usecases.benchmark import AlgorithmRunAsBackgroundTasksUcImpl
from luna_bench._internal.usecases.benchmark.protocols import (
    BackgroundRunAlgorithmAsyncUc,
    BackgroundRunAlgorithmSyncUc,
)
from luna_bench.entities import JobStatus
from tests.unit.fixtures.mock_database import SetupBenchmark


class TestAlgorithmRunAsBackgroundTask:
    def test_run_as_background_task(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        benchmark_result = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark)
        assert is_successful(benchmark_result), "Failed to load benchmark"
        benchmark = benchmark_result.unwrap()
        assert benchmark.modelset is not None, "Failed to load modelset"

        mock_start_async = MagicMock(spec=BackgroundRunAlgorithmAsyncUc)
        mock_start_sync = MagicMock(spec=BackgroundRunAlgorithmSyncUc)
        mock_start_async.return_value = "taskId"
        mock_start_sync.return_value = "taskId"

        uc = AlgorithmRunAsBackgroundTasksUcImpl(
            background_start_async=mock_start_async,
            background_start_sync=mock_start_sync,
            transaction=setup_benchmark.transaction,
        )

        uc(
            benchmark_name=benchmark.name,
            models=benchmark.modelset.models,
            algorithms=benchmark.algorithms,
        )

        models_nr = len(benchmark.modelset.models)
        assert len(benchmark.algorithms) > 0, "For this test to make sense, there should be at least one algorithm"
        assert models_nr > 0, "For this test to make sense, there should be at least one model"
        # Check user model
        for a in benchmark.algorithms:
            assert len(a.results) == models_nr
            for v in a.results.values():
                assert v.task_id == "taskId"
                assert v.status == JobStatus.RUNNING

        # Check stored model
        with setup_benchmark.transaction as t:
            benchmark_domain = t.benchmark.load(benchmark.name).unwrap()

        for b in benchmark_domain.algorithms:
            assert len(b.results) == models_nr
            for w in b.results.values():
                assert w.task_id == "taskId"
                assert w.status == JobStatus.RUNNING
