"""An algorithm asked to repeat has to run that often, and stay one entry while doing it."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any

import pytest
from luna_model import Model, Solution

from luna_bench import Benchmark, ModelSet
from luna_bench._internal.background_tasks.huey.huey_algorithm_runner import HueyAlgorithmRunner
from luna_bench.algorithms.variants import ParameterGrid
from luna_bench.custom import BaseAlgorithmSync, BaseMetric, MetricResult, algorithm, metric, plot
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.entities.enums import JobStatus
from luna_bench.plots.dimensions import MetricDimension
from luna_bench.plots.generics.metric_bar_plot import MetricBarPlot
from tests.utils.luna_model import simple_model

if TYPE_CHECKING:
    from collections.abc import Generator
    from unittest.mock import MagicMock

    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


#: Counts the solves of a test run, so the repetitions of one model can be told apart.
#: A module-level counter rather than a class attribute: on a pydantic model that would
#: be a private attribute, and every run is handed its own copy of the algorithm anyway.
_counter = itertools.count()


@algorithm
class CountingAlgorithm(BaseAlgorithmSync):
    """Reports which call it is, so the runs of one model can be told apart."""

    #: Varied by the grid test; the algorithm itself does nothing with it.
    calls: int = 0

    def run(self, model: Model) -> tuple[Solution, dict[str, Any]]:
        solution = Solution.from_dict(data=dict.fromkeys(model.variables(), 1), env=model.environment)
        return solution, {"call": next(_counter)}


class SampleCountResult(MetricResult):
    samples: int


@metric
class SampleCountMetric(BaseMetric[SampleCountResult]):
    """Counts the samples of a solution - enough to show the metric ran on every run."""

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> SampleCountResult:  # noqa: ARG002
        return SampleCountResult(samples=len(solution.samples))


@plot(SampleCountMetric)
class SampleCountPlot(MetricBarPlot):
    """Bar plot of that metric, to see what the runs look like from a figure's side."""

    y: MetricDimension = MetricDimension("samples", "Samples")


class _Queue:
    """Stands in for huey: runs the task in-process, but through the real worker function."""

    def __init__(self) -> None:
        self._submitted: dict[str, tuple[BaseAlgorithmSync, int, str]] = {}

    def run_sync(self, algorithm: BaseAlgorithmSync, model_id: int, algorithm_name: str) -> str:
        task_id = f"task-{len(self._submitted)}"
        self._submitted[task_id] = (algorithm, model_id, algorithm_name)
        return task_id

    def retrieve_task_result(self, task_id: str) -> Any:  # noqa: ANN401 # Whatever the task returned.
        return HueyAlgorithmRunner._run_sync(*self._submitted[task_id])  # the real worker entry point

    @property
    def submitted(self) -> dict[str, tuple[BaseAlgorithmSync, int, str]]:
        return self._submitted


@pytest.fixture()
def queue(bg_algorithm_runner: MagicMock) -> Generator[_Queue]:
    q = _Queue()
    bg_algorithm_runner.run_sync.side_effect = q.run_sync
    bg_algorithm_runner.retrieve_task_result.side_effect = q.retrieve_task_result
    yield q
    # The runner mock lives in the container for the whole session, and `reset_mock`
    # leaves side effects in place, so they are taken back out here.
    bg_algorithm_runner.run_sync.side_effect = None
    bg_algorithm_runner.retrieve_task_result.side_effect = None


class TestAlgorithmRepetitions:
    @staticmethod
    def _benchmark(name: str, models: int = 1) -> Benchmark:
        modelset = ModelSet.create(f"{name}_modelset")
        for i in range(models):
            modelset.add(simple_model(f"model_{i}"))

        benchmark = Benchmark.create(name)
        benchmark.set_modelset(modelset)
        return benchmark

    def test_every_repetition_is_its_own_run(self, queue: _Queue) -> None:
        benchmark = self._benchmark("repetitions_benchmark")
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=4)

        benchmark.run_algorithms()

        runs = benchmark.get_algorithm("counting").results["model_0"]
        assert [r.repetition for r in runs] == [0, 1, 2, 3]
        assert all(r.status == JobStatus.DONE for r in runs)
        # Four jobs went to the queue, rather than one result being written four times.
        assert len(queue.submitted) == 4
        # Every run reported its own call, so the four are genuinely separate solves.
        assert len({r.metadata["call"] for r in runs if r.metadata is not None}) == 4

    def test_the_runs_survive_a_reload(self, queue: _Queue) -> None:
        _ = queue
        benchmark = self._benchmark("reload_benchmark")
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=3)
        benchmark.run_algorithms()

        reloaded = Benchmark.load("reload_benchmark")
        entry = reloaded.get_algorithm("counting")

        assert entry.repetitions == 3
        assert [r.repetition for r in entry.results["model_0"]] == [0, 1, 2]
        assert [r.solution is not None for r in entry.results["model_0"]] == [True, True, True]

    def test_a_metric_is_evaluated_once_per_run(self, queue: _Queue) -> None:
        _ = queue
        benchmark = self._benchmark("metric_benchmark")
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=3)
        benchmark.add_metric("samples", SampleCountMetric())

        benchmark.run_algorithms()
        benchmark.run_metrics()

        results = Benchmark.load("metric_benchmark").get_metric("samples").results["model_0"]["counting"]
        assert [r.repetition for r in results] == [0, 1, 2]
        assert all(r.status == JobStatus.DONE for r in results)

    def test_the_exported_table_has_a_row_per_run(self, queue: _Queue) -> None:
        _ = queue
        benchmark = self._benchmark("export_repetitions_benchmark", models=2)
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=3)
        benchmark.add_metric("samples", SampleCountMetric())

        benchmark.run()

        df = benchmark.to_dataframe()
        assert len(df) == 2 * 3
        assert sorted(df.loc[df["model"] == "model_0", "repetition"]) == [0, 1, 2]
        assert df["samples/samples"].notna().all()

    def test_a_plot_aggregates_over_every_run(self, queue: _Queue) -> None:
        """The runs are rows of their own, which is what makes the error bars mean something."""
        _ = queue
        benchmark = self._benchmark("plot_repetitions_benchmark", models=2)
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=3)
        benchmark.add_metric("samples", SampleCountMetric())

        benchmark.run_algorithms()
        benchmark.run_metrics()

        rows = SampleCountPlot().rows(BenchmarkResultContainer.from_benchmark(benchmark))

        assert len(rows) == 2 * 3
        assert {row["algorithm"] for row in rows} == {"counting"}

    def test_running_again_adds_nothing(self, queue: _Queue) -> None:
        """A finished benchmark is not re-run, however often repetitions are asked for."""
        benchmark = self._benchmark("rerun_benchmark")
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=2)

        benchmark.run_algorithms()
        benchmark.run_algorithms()

        assert len(queue.submitted) == 2
        assert len(benchmark.get_algorithm("counting").results["model_0"]) == 2

    def test_a_single_run_is_still_a_single_run(self, queue: _Queue) -> None:
        """The default stays what it was: one run per model, numbered 0."""
        _ = queue
        benchmark = self._benchmark("default_benchmark")
        benchmark.add_algorithm("counting", CountingAlgorithm())

        benchmark.run_algorithms()

        entry = benchmark.get_algorithm("counting")
        assert entry.repetitions == 1
        assert [r.repetition for r in entry.results["model_0"]] == [0]
        assert entry.run("model_0") is entry.results["model_0"][0]

    def test_each_variant_is_repeated(self, queue: _Queue) -> None:
        benchmark = self._benchmark("variant_repetitions_benchmark")
        grid = benchmark.add_algorithm(
            "counting", CountingAlgorithm(), variants=ParameterGrid({"calls": [1, 2]}), repetitions=2
        )

        benchmark.run_algorithms()

        assert [entity.repetitions for entity in grid.entities] == [2, 2]
        # Two variants, two runs each.
        assert len(queue.submitted) == 4
        for entity in grid.entities:
            assert [r.repetition for r in benchmark.get_algorithm(entity.name).results["model_0"]] == [0, 1]

    def test_repetitions_below_one_are_refused(self) -> None:
        benchmark = self._benchmark("invalid_benchmark")

        with pytest.raises(ValueError, match="at least once"):
            benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=0)

    def test_the_stored_count_wins_when_an_entry_is_added_again(self, queue: _Queue) -> None:
        """Re-adding an algorithm keeps the entry it already has, repetitions included."""
        _ = queue
        benchmark = self._benchmark("readd_benchmark")
        benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=2)

        again = benchmark.add_algorithm("counting", CountingAlgorithm(), repetitions=5)

        assert again.repetitions == 2
