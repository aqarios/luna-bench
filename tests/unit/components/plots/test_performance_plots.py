"""Tests for the concrete performance plot `run` implementations."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from luna_bench.custom import BaseMetric, MetricResult
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.metrics import (
    ApproximationRatio,
    BestSolutionFoundRatio,
    FeasibilityRatio,
    FractionOfOverallBestSolution,
    Runtime,
    TimeToSolution,
)
from luna_bench.metrics.approximation_ratio import ApproximationRatioResult
from luna_bench.metrics.best_solution_found_ratio import BestSolutionFoundRatioResult
from luna_bench.metrics.feasbility_ratio import FeasibilityRatioResult
from luna_bench.metrics.fraction_of_overall_best_solution import FractionOfOverallBestSolutionResult
from luna_bench.metrics.runtime import RuntimeResult
from luna_bench.metrics.time_to_solution import TimeToSolutionResult
from luna_bench.plots.generics.bar_plot import BarPlot
from luna_bench.plots.performance import (
    AverageApproximationRatioPlot,
    AverageBestSolutionFoundRatioPlot,
    AverageFeasibilityRatioPlot,
    AverageFoBRatioPlot,
    AverageFractionOfOverallBestSolutionPlot,
    AverageRuntimePlot,
    AverageTimeToSolutionPlot,
    RuntimePerModelPlot,
)

RUN_CASES = [
    pytest.param(
        AverageRuntimePlot,
        Runtime,
        RuntimeResult(runtime_seconds=1.5),
        {"algorithm": "algo_1", "model": "model_a", "runtime_seconds": 1.5},
        {
            "x": "algorithm",
            "y": "runtime_seconds",
            "title": "Average Runtime per Solver",
            "xlabel": "Algorithm",
            "ylabel": "Runtime (s)",
        },
        id="average_runtime",
    ),
    pytest.param(
        RuntimePerModelPlot,
        Runtime,
        RuntimeResult(runtime_seconds=1.5),
        {"model": "model_a", "algorithm": "algo_1", "runtime_seconds": 1.5},
        {
            "x": "model",
            "y": "runtime_seconds",
            "hue": "algorithm",
            "xlabel": "Model",
            "ylabel": "Runtime (s)",
            "title": "Runtime per Model by Algorithm",
            "legend": True,
        },
        id="runtime_per_model",
    ),
    pytest.param(
        AverageApproximationRatioPlot,
        ApproximationRatio,
        ApproximationRatioResult(approximation_ratio=0.9),
        {"algorithm": "algo_1", "model": "model_a", "approximation_ratio": 0.9},
        {
            "x": "algorithm",
            "y": "approximation_ratio",
            "xlabel": "Algorithm",
            "ylabel": "Approximation Ratio",
            "title": "Average Approximation Ratio per Solver (1.0 = optimal)",
            "hline": 1.0,
            "hline_label": "Optimal (1.0)",
        },
        id="average_approximation_ratio",
    ),
    pytest.param(
        AverageBestSolutionFoundRatioPlot,
        BestSolutionFoundRatio,
        BestSolutionFoundRatioResult(best_solution_found=1.2),
        {"algorithm": "algo_1", "model": "model_a", "time_to_solution": 1.2},
        {
            "x": "algorithm",
            "y": "time_to_solution",
            "xlabel": "Algorithm",
            "ylabel": "Best Solution Found Ratio",
            "title": "Average Time to Solution per Algorithm (higher is better)",
        },
        id="average_best_solution_found_ratio",
    ),
    pytest.param(
        AverageFeasibilityRatioPlot,
        FeasibilityRatio,
        FeasibilityRatioResult(feasibility_ratio=0.75),
        {"algorithm": "algo_1", "model": "model_a", "feasibility_ratio": 0.75},
        {
            "x": "algorithm",
            "y": "feasibility_ratio",
            "xlabel": "Algorithm",
            "title": "Average Feasibility Ratio per Solver",
            "ylabel": "Feasibility Ratio",
            "ylim": (0, 1.15),
            "hline": 1.0,
            "hline_label": "Upper Limit (1.0)",
        },
        id="average_feasibility_ratio",
    ),
    pytest.param(
        AverageFractionOfOverallBestSolutionPlot,
        FractionOfOverallBestSolution,
        FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=0.6),
        {"algorithm": "algo_1", "model": "model_a", "best_solution_found": 0.6},
        {
            "x": "algorithm",
            "y": "best_solution_found",
            "xlabel": "Algorithm",
            "ylabel": "Best Solution Found",
            "title": "Average best solution found per Solver (1.0 = optimal)",
            "hline": 1.0,
            "hline_label": "Optimal (1.0)",
        },
        id="average_fob",
    ),
    pytest.param(
        AverageFoBRatioPlot,
        FractionOfOverallBestSolution,
        FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=0.6),
        {"algorithm": "algo_1", "model": "model_a", "fraction_of_overall_best": 0.6},
        {
            "x": "algorithm",
            "y": "fraction_of_overall_best",
            "xlabel": "Algorithm",
            "ylabel": "Fraction of overall best solution",
            "title": "Average Fraction of overall best Ratio per Solver (1.0 = optimal)",
            "hline": 1.0,
            "hline_label": "Optimal (1.0)",
        },
        id="average_fob_ratio",
    ),
    pytest.param(
        AverageTimeToSolutionPlot,
        TimeToSolution,
        TimeToSolutionResult(time_to_solution=2.5, probability_optimal=0.5, num_optimal_found=5, num_samples=10),
        {"algorithm": "algo_1", "model": "model_a", "time_to_solution": 2.5},
        {
            "x": "algorithm",
            "y": "time_to_solution",
            "xlabel": "Algorithm",
            "ylabel": "Time to Solution (TTS)",
            "title": "Average Time to Solution per Algorithm (lower is better)",
        },
        id="average_time_to_solution",
    ),
]


class TestPerformancePlotRun:
    """Test that each performance plot builds rows and delegates to `create`."""

    @pytest.mark.parametrize(("plot_cls", "metric_cls", "metric_result", "expected_row", "expected_kwargs"), RUN_CASES)
    def test_run_builds_rows_and_calls_create(
        self,
        plot_cls: type[BarPlot],
        metric_cls: type[BaseMetric[Any]],
        metric_result: MetricResult,
        expected_row: dict[str, Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        """Test run queries the matching metric type and forwards rows to create."""
        plot_instance = plot_cls()
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = [("model_a", "algo_1", metric_result)]

        with patch.object(plot_cls, "create") as mock_create:
            plot_instance.run(benchmark_results, save_dir="out")

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(metric_cls)
        mock_create.assert_called_once_with(save_dir="out", rows=[expected_row], **expected_kwargs)

    @pytest.mark.parametrize(("plot_cls", "metric_cls", "metric_result", "expected_row", "expected_kwargs"), RUN_CASES)
    def test_run_with_no_metric_results_passes_empty_rows(
        self,
        plot_cls: type[BarPlot],
        metric_cls: type[BaseMetric[Any]],
        metric_result: MetricResult,
        expected_row: dict[str, Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        """Test run passes empty rows to create when no metric results exist."""
        _ = metric_result, expected_row
        plot_instance = plot_cls()
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = []

        with patch.object(plot_cls, "create") as mock_create:
            plot_instance.run(benchmark_results, save_dir=None)

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(metric_cls)
        mock_create.assert_called_once_with(save_dir=None, rows=[], **expected_kwargs)
