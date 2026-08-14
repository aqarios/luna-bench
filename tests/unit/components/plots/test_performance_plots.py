"""Tests for the concrete performance plot `run` implementations."""

from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest

from luna_bench.custom import BaseMetric, MetricResult
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.metrics import (
    ApproximationRatio,
    BestSolutionFoundRatio,
    FeasibilityRatio,
    FeasibleSamples,
    FractionOfOverallBestSolution,
    Runtime,
    TimeToSolution,
)
from luna_bench.metrics.approximation_ratio import ApproximationRatioResult
from luna_bench.metrics.best_solution_found_ratio import BestSolutionFoundRatioResult
from luna_bench.metrics.feasbility_ratio import FeasibilityRatioResult
from luna_bench.metrics.feasible_samples import FeasibleSamplesResult
from luna_bench.metrics.fraction_of_overall_best_solution import FractionOfOverallBestSolutionResult
from luna_bench.metrics.runtime import RuntimeResult
from luna_bench.metrics.time_to_solution import TimeToSolutionResult
from luna_bench.plots.dimensions import ModelDimension
from luna_bench.plots.generics.bar_plot import BarPlot
from luna_bench.plots.performance import (
    ApproximationRatioPlot,
    BestSolutionFoundRatioPlot,
    FeasibilityRatioPlot,
    FeasibleSampleRatioPlot,
    FeasibleSolutionFoundPlot,
    FractionOfOverallBestSolutionPlot,
    RuntimePerModelPlot,
    RuntimePlot,
    TimeToSolutionPlot,
)
from luna_bench.plots.utils import AUTO_ERRORBAR, Aggregation

#: The display configuration every metric bar plot passes on, unless it declares its own.
BASE_KWARGS: dict[str, Any] = {
    "x": "algorithm",
    "xlabel": "Algorithm",
    "aggregation": Aggregation.MEAN,
    "errorbar": AUTO_ERRORBAR,
    "hline": None,
    "hline_label": None,
    "baseline": None,
    "ylim": None,
}

RUN_CASES = [
    pytest.param(
        RuntimePlot,
        Runtime,
        RuntimeResult(runtime_seconds=1.5),
        {"algorithm": "algo_1", "model": "model_a", "runtime_seconds": 1.5},
        {
            "title": "Runtime per Solver",
            "baseline": 0.0,
            "y": "runtime_seconds",
            "ylabel": "Runtime (s)",
        },
        id="runtime",
    ),
    pytest.param(
        RuntimePerModelPlot,
        Runtime,
        RuntimeResult(runtime_seconds=1.5),
        {"model": "model_a", "algorithm": "algo_1", "runtime_seconds": 1.5},
        {
            "hue": "algorithm",
            "x": "model",
            "xlabel": "Model",
            "title": "Runtime per Model by Algorithm",
            "legend": True,
            "baseline": 0.0,
            "y": "runtime_seconds",
            "ylabel": "Runtime (s)",
        },
        id="runtime_per_model",
    ),
    pytest.param(
        ApproximationRatioPlot,
        ApproximationRatio,
        ApproximationRatioResult(approximation_ratio=0.9),
        {"algorithm": "algo_1", "model": "model_a", "approximation_ratio": 90.0},
        {
            "title": "Approximation Ratio per Solver (1.0 = optimal)",
            "hline": 100.0,
            "hline_label": "Optimal (100%)",
            "y": "approximation_ratio",
            "ylabel": "Approximation Ratio [%]",
        },
        id="approximation_ratio",
    ),
    pytest.param(
        BestSolutionFoundRatioPlot,
        BestSolutionFoundRatio,
        BestSolutionFoundRatioResult(best_solution_found=1.2),
        {"algorithm": "algo_1", "model": "model_a", "best_solution_found": 120.0},
        {
            "title": "Best Solution Found Ratio per Solver (100% = optimal)",
            "hline": 100.0,
            "hline_label": "Optimal (100%)",
            "baseline": 0.0,
            "y": "best_solution_found",
            "ylabel": "Best Solution Found Ratio [%]",
        },
        id="best_solution_found_ratio",
    ),
    pytest.param(
        FeasibilityRatioPlot,
        FeasibilityRatio,
        FeasibilityRatioResult(feasibility_ratio=0.75),
        {"algorithm": "algo_1", "model": "model_a", "feasibility_ratio": 75.0},
        {
            "title": "Feasibility Ratio per Solver",
            "ylim": (0, 100.0),
            "hline": 100.0,
            "hline_label": "Upper Limit (100%)",
            "y": "feasibility_ratio",
            "ylabel": "Feasibility Ratio [%]",
        },
        id="feasibility_ratio",
    ),
    pytest.param(
        FeasibleSolutionFoundPlot,
        FeasibilityRatio,
        FeasibilityRatioResult(feasibility_ratio=0.75),
        {"algorithm": "algo_1", "model": "model_a", "feasibility_ratio": 100.0},
        {
            "title": "Models with a Feasible Solution per Algorithm",
            "ylim": (0, 100.0),
            "hline": 100.0,
            "hline_label": "Upper Limit (100%)",
            "y": "feasibility_ratio",
            "ylabel": "Feasible solution found [% of models]",
        },
        id="feasible_solution_found",
    ),
    pytest.param(
        FeasibleSampleRatioPlot,
        FeasibleSamples,
        FeasibleSamplesResult(num_feasible_samples=3, num_samples=4),
        {"algorithm": "algo_1", "feasible_sample_ratio": 75.0},
        {
            "title": "Share of Feasible Samples per Solver (pooled over models)",
            "ylim": (0, 100.0),
            "errorbar": None,
            "hline": 100.0,
            "hline_label": "Upper Limit (100%)",
            "y": "feasible_sample_ratio",
            "ylabel": "Feasible Samples / All Samples [%]",
        },
        id="feasible_sample_ratio",
    ),
    pytest.param(
        FractionOfOverallBestSolutionPlot,
        FractionOfOverallBestSolution,
        FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=0.6),
        {"algorithm": "algo_1", "model": "model_a", "fraction_of_overall_best_solution": 60.0},
        {
            "title": "Best Solution Found per Solver (100% = optimal)",
            "ylim": (0, 100.0),
            "hline": 100.0,
            "hline_label": "Optimal (100%)",
            "baseline": 0.0,
            "y": "fraction_of_overall_best_solution",
            "ylabel": "Best Solution Found [%]",
        },
        id="average_fob",
    ),
    pytest.param(
        TimeToSolutionPlot,
        TimeToSolution,
        TimeToSolutionResult(time_to_solution=2.5, probability_optimal=0.5, num_optimal_found=5, num_samples=10),
        {"algorithm": "algo_1", "model": "model_a", "time_to_solution": 2.5},
        {
            "title": "Time to Solution per Algorithm (lower is better)",
            "baseline": 0.0,
            "y": "time_to_solution",
            "ylabel": "Time to Solution (TTS)",
        },
        id="time_to_solution",
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
        mock_create.assert_called_once_with(save_dir="out", rows=[expected_row], **{**BASE_KWARGS, **expected_kwargs})

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

        # Without rows there is nothing to split, so a grouped plot passes no hue either.
        expected = {k: v for k, v in {**BASE_KWARGS, **expected_kwargs}.items() if k not in {"hue", "legend"}}

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(metric_cls)
        mock_create.assert_called_once_with(save_dir=None, rows=[], **expected)


class TestFeasibleSampleRatioPlot:
    """Test the pooling of the per-model sample counts into one ratio per bar."""

    def test_run_pools_counts_across_models(self) -> None:
        """Test the ratio divides summed feasible samples by summed total samples."""
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = [
            ("model_a", "algo_1", FeasibleSamplesResult(num_feasible_samples=1, num_samples=10)),
            ("model_b", "algo_1", FeasibleSamplesResult(num_feasible_samples=90, num_samples=90)),
            ("model_a", "algo_2", FeasibleSamplesResult(num_feasible_samples=0, num_samples=10)),
        ]

        with patch.object(FeasibleSampleRatioPlot, "create") as mock_create:
            FeasibleSampleRatioPlot().run(benchmark_results)

        # Pooling weights samples, not models: 91/100 rather than the per-model mean of 55%.
        assert mock_create.call_args.kwargs["rows"] == [
            {"algorithm": "algo_1", "feasible_sample_ratio": 91.0},
            {"algorithm": "algo_2", "feasible_sample_ratio": 0.0},
        ]

    def test_run_reports_zero_when_no_samples_were_returned(self) -> None:
        """Test an algorithm without any sample gets a zero bar instead of a division error."""
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = [
            ("model_a", "algo_1", FeasibleSamplesResult(num_feasible_samples=0, num_samples=0))
        ]

        with patch.object(FeasibleSampleRatioPlot, "create") as mock_create:
            FeasibleSampleRatioPlot().run(benchmark_results)

        assert mock_create.call_args.kwargs["rows"] == [{"algorithm": "algo_1", "feasible_sample_ratio": 0.0}]

    def test_run_pools_within_each_group(self) -> None:
        """Test a grouped plot keeps one pooled bar per algorithm and group."""
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = [
            ("model_a", "algo_1", FeasibleSamplesResult(num_feasible_samples=1, num_samples=4)),
            ("model_b", "algo_1", FeasibleSamplesResult(num_feasible_samples=3, num_samples=4)),
        ]

        def group_by_model(_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> dict[str, Any]:
            for row in rows:
                row["Use case"] = f"case_{row['model']}"
            return {"hue": "Use case", "legend": True}

        with (
            patch.object(FeasibleSampleRatioPlot, "create") as mock_create,
            patch.object(FeasibleSampleRatioPlot, "apply_grouping", side_effect=group_by_model),
        ):
            FeasibleSampleRatioPlot().run(benchmark_results)

        assert mock_create.call_args.kwargs["rows"] == [
            {"algorithm": "algo_1", "feasible_sample_ratio": 25.0, "Use case": "case_model_a"},
            {"algorithm": "algo_1", "feasible_sample_ratio": 75.0, "Use case": "case_model_b"},
        ]
        assert mock_create.call_args.kwargs["hue"] == "Use case"


class TestFeasibleSolutionFoundPlot:
    """Test the feasibility indicator derived from the feasibility ratio."""

    @pytest.mark.parametrize(("feasibility_ratio", "expected"), [(0.0, 0.0), (0.01, 100.0), (1.0, 100.0)])
    def test_run_maps_any_feasible_sample_to_full_percent(self, feasibility_ratio: float, expected: float) -> None:
        """Test a model counts fully when at least one sample was feasible."""
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = [
            ("model_a", "algo_1", FeasibilityRatioResult(feasibility_ratio=feasibility_ratio))
        ]

        with patch.object(FeasibleSolutionFoundPlot, "create") as mock_create:
            FeasibleSolutionFoundPlot().run(benchmark_results)

        assert mock_create.call_args.kwargs["rows"] == [
            {"algorithm": "algo_1", "model": "model_a", "feasibility_ratio": expected}
        ]


class TestFeasibleSampleRatioPooling:
    """Test what the pooled ratio is pooled over."""

    @staticmethod
    def _results() -> MagicMock:
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.get_all_metrics_of_type.return_value = [
            ("model_a", "algo_1", FeasibleSamplesResult(num_feasible_samples=1, num_samples=10)),
            ("model_b", "algo_1", FeasibleSamplesResult(num_feasible_samples=9, num_samples=10)),
        ]
        return benchmark_results

    def test_the_models_are_pooled_into_one_bar_per_algorithm(self) -> None:
        """Test the point of the plot: every sample counts the same, whichever model it is from."""
        with patch.object(FeasibleSampleRatioPlot, "create") as mock_create:
            FeasibleSampleRatioPlot().run(self._results())

        assert mock_create.call_args.kwargs["rows"] == [{"algorithm": "algo_1", "feasible_sample_ratio": 50.0}]

    def test_a_plot_drawn_per_model_pools_within_the_model(self) -> None:
        """Test the bars keep what tells them apart, so any dimension can be the x-axis."""
        with patch.object(FeasibleSampleRatioPlot, "create") as mock_create:
            FeasibleSampleRatioPlot(x=ModelDimension()).run(self._results())

        assert mock_create.call_args.kwargs["x"] == "model"
        assert mock_create.call_args.kwargs["rows"] == [
            {"model": "model_a", "feasible_sample_ratio": 10.0},
            {"model": "model_b", "feasible_sample_ratio": 90.0},
        ]


class TestTimeBaselines:
    """Test the line the bars of a plot measured in seconds stand on."""

    TIME_PLOTS: ClassVar[list[type]] = [RuntimePlot, RuntimePerModelPlot, TimeToSolutionPlot]

    @pytest.mark.parametrize("plot_cls", TIME_PLOTS)
    def test_the_bars_stand_on_a_line_at_zero(self, plot_cls: type) -> None:
        """Test a time has a floor, and the figure says where it is."""
        assert plot_cls().y.baseline == 0.0

    @pytest.mark.parametrize("plot_cls", TIME_PLOTS)
    def test_the_line_carries_no_label(self, plot_cls: type) -> None:
        """Test it reads as the floor of the bars, not as a target competing with one."""
        plot = plot_cls()

        assert plot.y.reference is None
        assert plot.y.reference_label is None
