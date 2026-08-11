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
from luna_bench.plots.generics.parameter_sweep_plot import ParameterSweepPlot
from luna_bench.plots.plot_style import Figure


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
    """Test that the swept value is read off the algorithm configuration."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_rows_pair_the_parameter_with_the_metric(self) -> None:
        """Test each row carries the configured parameter and the measured value."""
        benchmark_results = _benchmark_results(
            [
                ("model_a", "qaoa_p1", ApproximationRatioResult(approximation_ratio=0.5)),
                ("model_a", "qaoa_p3", ApproximationRatioResult(approximation_ratio=0.9)),
            ],
            {"qaoa_p1": SimpleNamespace(reps=1), "qaoa_p3": SimpleNamespace(reps=3)},
        )

        rows = ApproximationRatioVsParameterPlot(parameter="reps").rows(benchmark_results)

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(ApproximationRatio)
        assert rows == [
            {"reps": 1.0, "approximation_ratio": 0.5, "model": "model_a", "algorithm": "qaoa_p1"},
            {"reps": 3.0, "approximation_ratio": 0.9, "model": "model_a", "algorithm": "qaoa_p3"},
        ]

    @pytest.mark.parametrize(
        "configuration", [SimpleNamespace(), SimpleNamespace(reps=True), SimpleNamespace(reps="3")]
    )
    def test_algorithms_without_a_numeric_parameter_are_left_out(self, configuration: object) -> None:
        """Test a classical baseline in the same benchmark does not break the sweep."""
        benchmark_results = _benchmark_results(
            [("model_a", "scip", RuntimeResult(runtime_seconds=1.0))],
            {"scip": configuration},
        )

        assert RuntimeVsParameterPlot(parameter="reps").rows(benchmark_results) == []

    def test_missing_algorithm_run_is_left_out(self) -> None:
        """Test a metric without a matching algorithm run contributes no point."""
        benchmark_results = _benchmark_results(
            [("model_a", "qaoa_p1", RuntimeResult(runtime_seconds=1.0))],
            {},
        )

        assert RuntimeVsParameterPlot().rows(benchmark_results) == []

    def test_run_without_any_sweep_warns_instead_of_drawing(self) -> None:
        """Test a benchmark that sweeps nothing is reported, not plotted empty."""
        plot_instance = RuntimeVsParameterPlot(parameter="reps")
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

    def test_run_draws_the_collected_rows(self) -> None:
        """Test the rows reach create once at least one algorithm carries the parameter."""
        plot_instance = ApproximationRatioVsParameterPlot(parameter="reps")
        benchmark_results = _benchmark_results(
            [("model_a", "qaoa_p2", ApproximationRatioResult(approximation_ratio=0.7))],
            {"qaoa_p2": SimpleNamespace(reps=2)},
        )

        with patch.object(ApproximationRatioVsParameterPlot, "create") as mock_create:
            plot_instance.run(benchmark_results, save_dir="out")

        mock_create.assert_called_once_with(
            rows=[{"reps": 2.0, "approximation_ratio": 0.7, "model": "model_a", "algorithm": "qaoa_p2"}],
            save_dir="out",
        )


class TestParameterSweepCreate:
    """Test the figure the sweep draws."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_create_labels_the_swept_values(self) -> None:
        """Test the x ticks are the measured values, not an arbitrary range."""
        plot_instance = ApproximationRatioVsParameterPlot(parameter="reps", figure=Figure(show=False))
        rows = [
            {"reps": 1.0, "approximation_ratio": 0.5, "model": "model_a", "algorithm": "qaoa_p1"},
            {"reps": 3.0, "approximation_ratio": 0.9, "model": "model_a", "algorithm": "qaoa_p3"},
        ]

        plot_instance.create(rows=rows)

        assert [tick.get_position()[0] for tick in plt.gca().get_xticklabels()] == [1.0, 3.0]
        assert plt.gca().get_xlabel() == "reps"

    def test_xlabel_overrides_the_parameter_name(self) -> None:
        """Test a sweep can be labelled in the terms of its algorithm."""
        plot_instance = ApproximationRatioVsParameterPlot(
            parameter="reps", xlabel="QAOA layers (p)", figure=Figure(show=False)
        )

        plot_instance.create(rows=[{"reps": 1.0, "approximation_ratio": 0.5, "model": "m", "algorithm": "a"}])

        assert plt.gca().get_xlabel() == "QAOA layers (p)"

    def test_without_hue_the_lines_collapse_into_one(self) -> None:
        """Test hue=None aggregates the models instead of drawing a line each."""
        plot_instance = RuntimeVsParameterPlot(hue=None, figure=Figure(show=False))
        rows = [
            {"reps": 1.0, "runtime_seconds": 1.0, "model": "model_a", "algorithm": "a"},
            {"reps": 1.0, "runtime_seconds": 3.0, "model": "model_b", "algorithm": "a"},
        ]

        plot_instance.create(rows=rows)

        assert plt.gca().get_legend() is None


class UndeclaredSweepPlot(ParameterSweepPlot):
    """A sweep that forgot its ``@plot(...)`` decorator."""

    required_metrics: ClassVar[list[Any]] = []


def test_sweep_without_a_declared_metric_raises() -> None:
    """Test a missing ``@plot(...)`` declaration is reported instead of guessed."""
    with pytest.raises(PlotMetricUndeclaredError):
        UndeclaredSweepPlot().rows(_benchmark_results([], {}))
