"""Tests for the parameter sweep plots."""

from types import SimpleNamespace
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest
from matplotlib import pyplot as plt

from luna_bench.custom.result_containers.algorithm_result_container import AlgorithmResultContainer
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.errors.components.plots import PlotMetricUndeclaredError
from luna_bench.metrics import ApproximationRatio
from luna_bench.metrics.approximation_ratio import ApproximationRatioResult
from luna_bench.metrics.runtime import RuntimeResult
from luna_bench.plots.analysis import ApproximationRatioVsParameterPlot, RuntimeVsParameterPlot
from luna_bench.plots.dimensions import AlgorithmDimension, ParameterDimension
from luna_bench.plots.generics.parameter_sweep_plot import ParameterSweepPlot
from luna_bench.plots.plot_style import Figure, Missing


def _benchmark_results(
    metric_results: list[tuple[str, str, object]],
    configurations: dict[str, object],
) -> MagicMock:
    """Return results whose algorithms carry the given configurations."""
    benchmark_results = MagicMock(spec=BenchmarkResultContainer)
    benchmark_results.get_all_metrics_of_type.return_value = metric_results
    benchmark_results.algorithms = {
        model_name: {
            algorithm_name: MagicMock(spec=AlgorithmResultContainer, algorithm=configuration)
            for algorithm_name, configuration in configurations.items()
        }
        for model_name, _, _ in metric_results
    }
    return benchmark_results


class TestParameterSweepRows:
    """Test the rows a sweep collects before its dimensions are resolved."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_rows_pair_each_result_with_the_run_it_came_from(self) -> None:
        """Test a row says what was measured and which run measured it, nothing more.

        Which of them belong on the axis is the dimension's decision, so the rows are
        collected without asking - they carry the model and the algorithm the dimensions
        look the rest up by.
        """
        benchmark_results = _benchmark_results(
            [
                ("model_a", "qaoa_p1", ApproximationRatioResult(approximation_ratio=0.5)),
                ("model_a", "qaoa_p3", ApproximationRatioResult(approximation_ratio=0.9)),
            ],
            {"qaoa_p1": SimpleNamespace(reps=1), "qaoa_p3": SimpleNamespace(reps=3)},
        )

        rows = ApproximationRatioVsParameterPlot(x=ParameterDimension("reps")).rows(benchmark_results)

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(ApproximationRatio)
        assert rows == [
            {"approximation_ratio": 50.0, "model": "model_a", "algorithm": "qaoa_p1"},
            {"approximation_ratio": 90.0, "model": "model_a", "algorithm": "qaoa_p3"},
        ]

    def test_sweep_without_a_declared_metric_raises(self) -> None:
        """Test a missing ``@plot(...)`` declaration is reported instead of guessed."""
        with pytest.raises(PlotMetricUndeclaredError):
            UndeclaredSweepPlot().rows(_benchmark_results([], {}))


class TestParameterSweepRun:
    """Test what the dimensions make of those rows on the way to the figure."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_the_swept_value_reaches_create_as_a_number(self) -> None:
        """Test the x dimension puts the setting on the rows for the axis to space by."""
        plot_instance = ApproximationRatioVsParameterPlot(x=ParameterDimension("reps"))
        benchmark_results = _benchmark_results(
            [("model_a", "qaoa_p2", ApproximationRatioResult(approximation_ratio=0.7))],
            {"qaoa_p2": SimpleNamespace(reps=2)},
        )

        with patch.object(ApproximationRatioVsParameterPlot, "create") as mock_create:
            plot_instance.run(benchmark_results, save_dir="out")

        mock_create.assert_called_once_with(
            rows=[{"approximation_ratio": 70.0, "model": "model_a", "algorithm": "qaoa_p2", "reps": 2.0}],
            save_dir="out",
            hue="model",
        )

    @pytest.mark.parametrize(
        "configuration", [SimpleNamespace(), SimpleNamespace(reps=True), SimpleNamespace(reps="3")]
    )
    def test_algorithms_without_a_numeric_parameter_are_left_out(self, configuration: object) -> None:
        """Test a classical baseline in the same benchmark does not break the sweep."""
        plot_instance = RuntimeVsParameterPlot(x=ParameterDimension("reps"))
        benchmark_results = _benchmark_results(
            [
                ("model_a", "scip", RuntimeResult(runtime_seconds=1.0)),
                ("model_a", "qaoa_p2", RuntimeResult(runtime_seconds=2.0)),
            ],
            {"scip": configuration, "qaoa_p2": SimpleNamespace(reps=2)},
        )

        with patch.object(RuntimeVsParameterPlot, "create") as mock_create:
            plot_instance.run(benchmark_results)

        assert [row["algorithm"] for row in mock_create.call_args.kwargs["rows"]] == ["qaoa_p2"]

    def test_run_without_any_sweep_warns_instead_of_drawing(self) -> None:
        """Test a benchmark that sweeps nothing is reported, not plotted empty."""
        plot_instance = RuntimeVsParameterPlot(x=ParameterDimension("reps"))
        benchmark_results = _benchmark_results(
            [("model_a", "scip", RuntimeResult(runtime_seconds=1.0))],
            {"scip": SimpleNamespace()},
        )

        with (
            patch.object(plot_instance.logger, "warning") as mock_warning,
            patch.object(RuntimeVsParameterPlot, "create") as mock_create,
        ):
            plot_instance.run(benchmark_results)

        mock_warning.assert_called_once()
        mock_create.assert_not_called()

    def test_the_grouping_decides_what_a_line_is(self) -> None:
        """Test a line per algorithm is a grouping away, the same as on a bar plot."""
        plot_instance = RuntimeVsParameterPlot(x=ParameterDimension("reps"), grouping=AlgorithmDimension())
        benchmark_results = _benchmark_results(
            [("model_a", "qaoa_p2", RuntimeResult(runtime_seconds=2.0))],
            {"qaoa_p2": SimpleNamespace(reps=2)},
        )

        with patch.object(RuntimeVsParameterPlot, "create") as mock_create:
            plot_instance.run(benchmark_results)

        assert mock_create.call_args.kwargs["hue"] == "algorithm"

    def test_no_grouping_draws_a_single_line(self) -> None:
        """Test ``grouping=None`` aggregates the models rather than drawing a line each."""
        plot_instance = RuntimeVsParameterPlot(x=ParameterDimension("reps"), grouping=None)
        benchmark_results = _benchmark_results(
            [("model_a", "qaoa_p2", RuntimeResult(runtime_seconds=2.0))],
            {"qaoa_p2": SimpleNamespace(reps=2)},
        )

        with patch.object(RuntimeVsParameterPlot, "create") as mock_create:
            plot_instance.run(benchmark_results)

        assert "hue" not in mock_create.call_args.kwargs

    def test_a_grouping_that_does_not_apply_leaves_the_sweep_drawable(self) -> None:
        """Test lines that cannot be told apart are still worth drawing as one."""
        plot_instance = RuntimeVsParameterPlot(x=ParameterDimension("reps"), grouping=ParameterDimension("shots"))
        benchmark_results = _benchmark_results(
            [("model_a", "qaoa_p2", RuntimeResult(runtime_seconds=2.0))],
            {"qaoa_p2": SimpleNamespace(reps=2)},
        )

        with patch.object(RuntimeVsParameterPlot, "create") as mock_create:
            plot_instance.run(benchmark_results)

        mock_create.assert_called_once()
        assert "hue" not in mock_create.call_args.kwargs


class TestParameterSweepCreate:
    """Test the figure the sweep draws."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_create_labels_the_swept_values(self) -> None:
        """Test the x ticks are the measured values, not an arbitrary range."""
        plot_instance = ApproximationRatioVsParameterPlot(x=ParameterDimension("reps"), figure=Figure(show=False))
        rows = [
            {"reps": 1.0, "approximation_ratio": 50.0, "model": "model_a", "algorithm": "qaoa_p1"},
            {"reps": 3.0, "approximation_ratio": 90.0, "model": "model_a", "algorithm": "qaoa_p3"},
        ]

        plot_instance.create(rows=rows)

        assert [tick.get_position()[0] for tick in plt.gca().get_xticklabels()] == [1.0, 3.0]
        assert plt.gca().get_xlabel() == "reps"

    def test_a_label_on_the_x_dimension_titles_the_axis(self) -> None:
        """Test a sweep can be labelled in the terms of its algorithm."""
        plot_instance = ApproximationRatioVsParameterPlot(
            x=ParameterDimension("reps", label="QAOA layers (p)"), figure=Figure(show=False)
        )

        rows = [{"QAOA layers (p)": 1.0, "approximation_ratio": 0.5, "model": "m", "algorithm": "a"}]

        plot_instance.create(rows=rows)

        assert plt.gca().get_xlabel() == "QAOA layers (p)"

    def test_without_a_hue_the_lines_collapse_into_one(self) -> None:
        """Test an ungrouped sweep aggregates the models instead of drawing a line each."""
        plot_instance = RuntimeVsParameterPlot(figure=Figure(show=False))
        rows = [
            {"reps": 1.0, "runtime_seconds": 1.0, "model": "model_a", "algorithm": "a"},
            {"reps": 1.0, "runtime_seconds": 3.0, "model": "model_b", "algorithm": "a"},
        ]

        plot_instance.create(rows=rows)

        assert plt.gca().get_legend() is None

    def test_a_hue_draws_a_line_per_group(self) -> None:
        """Test the column the grouping resolved to is what the colours follow."""
        plot_instance = RuntimeVsParameterPlot(figure=Figure(show=False))
        rows = [
            {"reps": 1.0, "runtime_seconds": 1.0, "model": "model_a", "algorithm": "a"},
            {"reps": 1.0, "runtime_seconds": 3.0, "model": "model_b", "algorithm": "a"},
        ]

        plot_instance.create(rows=rows, hue="model")

        legend = plt.gca().get_legend()
        assert legend is not None
        assert [text.get_text() for text in legend.get_texts()] == ["model_a", "model_b"]

    def test_a_filled_value_is_counted_in_the_key(self) -> None:
        """Test a fabricated point says so, since a line has no slot to put a cross under.

        Without it a filled step is drawn as an ordinary point on the line and reads as a
        measurement, which is what the marks are for on a bar chart.
        """
        plot_instance = ApproximationRatioVsParameterPlot(
            x=ParameterDimension("reps"), figure=Figure(show=False), missing=Missing(policy="max")
        )
        rows = [
            {"reps": 1.0, "approximation_ratio": 50.0, "model": "model_a", "algorithm": "qaoa_p1"},
            {"reps": 3.0, "approximation_ratio": float("nan"), "model": "model_a", "algorithm": "qaoa_p3"},
        ]

        plot_instance.create(rows=rows)

        legend = plt.gca().get_legend()
        assert legend is not None
        assert "missing values (1)" in [text.get_text() for text in legend.get_texts()]

    def test_nothing_missing_leaves_the_key_alone(self) -> None:
        """Test the entry is about what happened, not a fixture of every sweep."""
        plot_instance = ApproximationRatioVsParameterPlot(x=ParameterDimension("reps"), figure=Figure(show=False))

        plot_instance.create(rows=[{"reps": 1.0, "approximation_ratio": 50.0, "model": "m", "algorithm": "a"}])

        legend = plt.gca().get_legend()
        assert legend is not None
        assert not any("missing" in text.get_text() for text in legend.get_texts())


class UndeclaredSweepPlot(ParameterSweepPlot):
    """A sweep that forgot its ``@plot(...)`` decorator."""

    required_metrics: ClassVar[list[Any]] = []
