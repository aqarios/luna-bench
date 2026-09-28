"""What a solver reports about a run has to survive the whole way to a metric and a table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from luna_model import Model, Solution

from luna_bench import Benchmark, ModelSet
from luna_bench._internal.background_tasks.huey.huey_algorithm_runner import HueyAlgorithmRunner
from luna_bench.custom import (
    BaseAlgorithmSync,
    BaseMetadataMetric,
    MetricResult,
    SolveMetadata,
    SolveOutcome,
    algorithm,
    metric,
)
from tests.utils.luna_model import simple_model

if TYPE_CHECKING:
    from collections.abc import Generator
    from unittest.mock import MagicMock

    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer

_METADATA = {"device": "qpu-7", "shots": 4096}


@algorithm
class ReportingAlgorithm(BaseAlgorithmSync):
    """Returns a solution together with what it knows about the run."""

    def run(self, model: Model) -> SolveOutcome:
        return Solution.from_dict(data=dict.fromkeys(model.variables(), 1), env=model.environment), _METADATA


@algorithm
class SilentAlgorithm(BaseAlgorithmSync):
    """Returns only a solution, the shape every algorithm had before metadata existed."""

    def run(self, model: Model) -> Solution:
        return Solution.from_dict(data=dict.fromkeys(model.variables(), 1), env=model.environment)


class DeviceResult(MetricResult):
    device: str
    shots: int


@metric
class DeviceMetric(BaseMetadataMetric[DeviceResult]):
    """Reports the device and shot count out of the metadata of the run."""

    def run_with_metadata(
        self,
        solution: Solution,  # noqa: ARG002
        feature_results: FeatureResultContainer,  # noqa: ARG002
        metadata: SolveMetadata,
    ) -> DeviceResult:
        return DeviceResult(device=metadata["device"], shots=metadata["shots"])


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


class TestSolverMetadataInBenchmark:
    @staticmethod
    def _benchmark(name: str) -> Benchmark:
        modelset = ModelSet.create(f"{name}_modelset")
        modelset.add(simple_model("a_model"))

        benchmark = Benchmark.create(name)
        benchmark.set_modelset(modelset)
        return benchmark

    def test_metadata_reaches_a_metric_and_survives_a_reload(self, queue: _Queue) -> None:
        _ = queue
        benchmark = self._benchmark("metadata_benchmark")
        benchmark.add_algorithm("reporting", ReportingAlgorithm())
        benchmark.add_metric("device", DeviceMetric())

        benchmark.run_algorithms()
        benchmark.run_metrics()

        result = benchmark.get_algorithm("reporting").results["a_model"]
        assert result.metadata == _METADATA

        # Reloaded from the database, so the bytes really made the round trip.
        reloaded = Benchmark.load("metadata_benchmark")
        assert reloaded.get_algorithm("reporting").results["a_model"].metadata == _METADATA

        metric_result = reloaded.get_metric("device").results["a_model"]["reporting"]
        assert metric_result.result is not None
        assert metric_result.result.model_dump() == {"device": "qpu-7", "shots": 4096}

    def test_an_algorithm_that_reports_nothing_leaves_the_metadata_empty(self, queue: _Queue) -> None:
        _ = queue
        benchmark = self._benchmark("silent_benchmark")
        benchmark.add_algorithm("silent", SilentAlgorithm())

        benchmark.run_algorithms()

        result = benchmark.get_algorithm("silent").results["a_model"]
        assert result.solution is not None
        assert result.metadata is None
        assert Benchmark.load("silent_benchmark").get_algorithm("silent").results["a_model"].metadata is None

    def test_a_metadata_metric_fails_only_for_the_run_that_reported_nothing(self, queue: _Queue) -> None:
        """One silent algorithm does not take the metric down for the reporting one."""
        _ = queue
        benchmark = self._benchmark("mixed_benchmark")
        benchmark.add_algorithm("reporting", ReportingAlgorithm())
        benchmark.add_algorithm("silent", SilentAlgorithm())
        benchmark.add_metric("device", DeviceMetric())

        benchmark.run_algorithms()
        benchmark.run_metrics()

        results = benchmark.get_metric("device").results["a_model"]
        assert results["reporting"].result is not None
        assert results["silent"].error is not None
        assert "No metadata is available" in results["silent"].error

    def test_the_exported_table_carries_the_metadata(self, queue: _Queue) -> None:
        _ = queue
        benchmark = self._benchmark("export_benchmark")
        benchmark.add_algorithm("reporting", ReportingAlgorithm())

        benchmark.run_algorithms()

        df = benchmark.to_dataframe()
        assert "metadata" in df.columns
        assert df.loc[df["algorithm"] == "reporting", "metadata"].tolist() == [_METADATA]
