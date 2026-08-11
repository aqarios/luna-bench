"""Tests for the declarative MetricBarPlot base."""

from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest

from luna_bench.custom import plot
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.errors.components.plots import PlotMetricUndeclaredError
from luna_bench.metrics import Runtime
from luna_bench.metrics.runtime import RuntimeResult
from luna_bench.plots.dimensions import MetricDimension, ModelDimension
from luna_bench.plots.generics.metric_bar_plot import MetricBarPlot
from luna_bench.plots.plot_style import Figure


@plot(Runtime)
class DeclaredMetricBarPlot(MetricBarPlot):
    """A plot that only declares what it reads and what it is called."""

    y: MetricDimension = MetricDimension("runtime_seconds", "Runtime (s)")
    figure: Figure = Figure(title="Runtime")


class UndeclaredMetricBarPlot(MetricBarPlot):
    """A plot that forgot its ``@plot(...)`` decorator."""

    required_metrics: ClassVar[list[Any]] = []


def _benchmark_results(*results: tuple[str, str, RuntimeResult]) -> MagicMock:
    benchmark_results = MagicMock(spec=BenchmarkResultContainer)
    benchmark_results.get_all_metrics_of_type.return_value = list(results)
    return benchmark_results


class TestMetricBarPlot:
    """Test that the declaration is enough to build and draw the rows."""

    def test_rows_carry_the_declared_value(self) -> None:
        """Test one row per model and algorithm, keyed by the declared column."""
        benchmark_results = _benchmark_results(
            ("model_a", "algo_1", RuntimeResult(runtime_seconds=1.5)),
            ("model_b", "algo_1", RuntimeResult(runtime_seconds=2.5)),
        )

        rows = DeclaredMetricBarPlot().rows(benchmark_results)

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(Runtime)
        assert rows == [
            {"algorithm": "algo_1", "model": "model_a", "runtime_seconds": 1.5},
            {"algorithm": "algo_1", "model": "model_b", "runtime_seconds": 2.5},
        ]

    def test_run_draws_the_rows(self) -> None:
        """Test run hands its rows to draw, which applies the declared configuration."""
        plot_instance = DeclaredMetricBarPlot()
        benchmark_results = _benchmark_results(("model_a", "algo_1", RuntimeResult(runtime_seconds=1.5)))

        with patch.object(DeclaredMetricBarPlot, "create") as mock_create:
            plot_instance.run(benchmark_results, save_dir="out")

        kwargs = mock_create.call_args.kwargs
        assert kwargs["y"] == "runtime_seconds"
        assert kwargs["title"] == "Runtime"
        assert kwargs["rows"] == [{"algorithm": "algo_1", "model": "model_a", "runtime_seconds": 1.5}]

    def test_declared_values_can_be_overridden_per_instance(self) -> None:
        """Test the declaration is a default, not a constant."""
        plot_instance = DeclaredMetricBarPlot(
            figure=Figure(title="Runtime, warm start"),
            y=MetricDimension("runtime_seconds", "Runtime (s)", limits=(0, 5)),
        )
        benchmark_results = _benchmark_results(("model_a", "algo_1", RuntimeResult(runtime_seconds=1.5)))

        with patch.object(DeclaredMetricBarPlot, "create") as mock_create:
            plot_instance.run(benchmark_results)

        assert mock_create.call_args.kwargs["title"] == "Runtime, warm start"
        assert mock_create.call_args.kwargs["ylim"] == (0, 5)

    def test_grouping_by_a_column_reaches_create(self) -> None:
        """Test group_by works for every metric bar plot, not only those that apply it."""
        plot_instance = DeclaredMetricBarPlot(grouping=ModelDimension())
        benchmark_results = _benchmark_results(("model_a", "algo_1", RuntimeResult(runtime_seconds=1.5)))

        with patch.object(DeclaredMetricBarPlot, "create") as mock_create:
            plot_instance.run(benchmark_results)

        assert mock_create.call_args.kwargs["hue"] == "model"
        assert mock_create.call_args.kwargs["legend"] is True

    def test_plot_without_a_declared_metric_raises(self) -> None:
        """Test a missing ``@plot(...)`` declaration is reported instead of guessed."""
        with pytest.raises(PlotMetricUndeclaredError):
            UndeclaredMetricBarPlot().rows(_benchmark_results())
