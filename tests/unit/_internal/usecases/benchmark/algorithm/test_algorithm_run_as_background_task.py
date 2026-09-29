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
            for runs in a.results.values():
                assert len(runs) == 1
                for v in runs:
                    assert v.task_id == "taskId"
                    assert v.status == JobStatus.RUNNING

        # Check stored model
        with setup_benchmark.transaction as t:
            benchmark_domain = t.benchmark.load(benchmark.name).unwrap()

        for b in benchmark_domain.algorithms:
            assert len(b.results) == models_nr
            for runs_domain in b.results.values():
                assert len(runs_domain) == 1
                for w in runs_domain:
                    assert w.task_id == "taskId"
                    assert w.status == JobStatus.RUNNING

    def test_one_job_per_repetition(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        """An algorithm asked to repeat queues that many runs per model, numbered from 0."""
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        assert benchmark.modelset is not None

        repetitions = 3
        for a in benchmark.algorithms:
            a.repetitions = repetitions

        uc = AlgorithmRunAsBackgroundTasksUcImpl(
            background_start_async=MagicMock(spec=BackgroundRunAlgorithmAsyncUc, return_value="taskId"),
            background_start_sync=MagicMock(spec=BackgroundRunAlgorithmSyncUc, return_value="taskId"),
            transaction=setup_benchmark.transaction,
        )
        uc(
            benchmark_name=benchmark.name,
            models=benchmark.modelset.models,
            algorithms=benchmark.algorithms,
        )

        for a in benchmark.algorithms:
            for runs in a.results.values():
                assert [r.repetition for r in runs] == list(range(repetitions))

        # And the same in the database, rather than only in the entity that queued them.
        with setup_benchmark.transaction as t:
            stored = t.benchmark.load(benchmark.name).unwrap()
        for b in stored.algorithms:
            for runs_domain in b.results.values():
                assert [r.repetition for r in runs_domain] == list(range(repetitions))

    def test_only_the_missing_repetitions_are_queued(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        """A run that already has a result is not started again, the ones missing are."""
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        assert benchmark.modelset is not None

        mock_start_sync = MagicMock(spec=BackgroundRunAlgorithmSyncUc, return_value="taskId")
        mock_start_async = MagicMock(spec=BackgroundRunAlgorithmAsyncUc, return_value="taskId")
        uc = AlgorithmRunAsBackgroundTasksUcImpl(
            background_start_async=mock_start_async,
            background_start_sync=mock_start_sync,
            transaction=setup_benchmark.transaction,
        )

        for a in benchmark.algorithms:
            a.repetitions = 2
        uc(benchmark_name=benchmark.name, models=benchmark.modelset.models, algorithms=benchmark.algorithms)
        first_round = mock_start_sync.call_count + mock_start_async.call_count

        # Asked again with one repetition more, only that one is started.
        for a in benchmark.algorithms:
            a.repetitions = 3
        uc(benchmark_name=benchmark.name, models=benchmark.modelset.models, algorithms=benchmark.algorithms)
        second_round = mock_start_sync.call_count + mock_start_async.call_count - first_round

        models_nr = len(benchmark.modelset.models)
        assert first_round == 2 * models_nr * len(benchmark.algorithms)
        assert second_round == models_nr * len(benchmark.algorithms)

    def test_a_run_queued_into_a_gap_keeps_the_list_ordered(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        """A failed repetition 0 that was reset is queued again and belongs first."""
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        assert benchmark.modelset is not None

        uc = AlgorithmRunAsBackgroundTasksUcImpl(
            background_start_async=MagicMock(spec=BackgroundRunAlgorithmAsyncUc, return_value="taskId"),
            background_start_sync=MagicMock(spec=BackgroundRunAlgorithmSyncUc, return_value="taskId"),
            transaction=setup_benchmark.transaction,
        )

        for a in benchmark.algorithms:
            a.repetitions = 3
        uc(benchmark_name=benchmark.name, models=benchmark.modelset.models, algorithms=benchmark.algorithms)

        # Drop repetition 0, as a reset of a failed run would.
        model_name = benchmark.modelset.models[0].name
        for a in benchmark.algorithms:
            a.results[model_name] = [r for r in a.results[model_name] if r.repetition != 0]

        uc(benchmark_name=benchmark.name, models=benchmark.modelset.models, algorithms=benchmark.algorithms)

        for a in benchmark.algorithms:
            assert [r.repetition for r in a.results[model_name]] == [0, 1, 2]
