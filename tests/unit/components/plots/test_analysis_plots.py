"""Tests for the analysis and property plot `run` implementations.

These plots differ from the performance plots in that they read a feature value per model
alongside the metric, so the row builders touch ``benchmark_results.features``.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from luna_bench.custom import BaseMetric, BasePlot, MetricResult
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.features import VarNumberFeature
from luna_bench.features.var_num_feature import VarNumberFeatureResult
from luna_bench.metrics import ApproximationRatio, FeasibilityRatio, Runtime
from luna_bench.metrics.approximation_ratio import ApproximationRatioResult
from luna_bench.metrics.feasbility_ratio import FeasibilityRatioResult
from luna_bench.metrics.runtime import RuntimeResult
from luna_bench.plots.analysis import (
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.plots.properties import VarNumberBarChartPlot
from luna_bench.plots.utils import AUTO_ERRORBAR, Aggregation

VAR_NUMBER = 12

RUN_CASES = [
    pytest.param(
        RuntimeVsVarNumberPlot,
        Runtime,
        RuntimeResult(runtime_seconds=1.5),
        {"algorithm": "algo_1", "model": "model_a", "var_number": VAR_NUMBER, "runtime_seconds": 1.5},
        {
            "x": "var_number",
            "y": "runtime_seconds",
            "xlabel": "Number of Variables",
            "ylabel": "Runtime (s)",
            "title": "Runtime vs Model Size",
            "hue": "algorithm",
        },
        id="runtime_vs_var_number",
    ),
    pytest.param(
        ApproximationRatioVsVarNumberPlot,
        ApproximationRatio,
        ApproximationRatioResult(approximation_ratio=0.9),
        {"algorithm": "algo_1", "model": "model_a", "x": VAR_NUMBER, "y": 0.9},
        {
            "xlabel": "Number of Variables",
            "ylabel": "Approximation Ratio",
            "title": "Approximation Ratio vs Number of Variables",
            "hue": "algorithm",
            "hline": 1.0,
            "hline_label": "Optimal (1.0)",
        },
        id="approximation_ratio_vs_var_number",
    ),
    pytest.param(
        FeasibilityRatioVsVarNumberPlot,
        FeasibilityRatio,
        FeasibilityRatioResult(feasibility_ratio=0.75),
        {"algorithm": "algo_1", "model": "model_a", "x": VAR_NUMBER, "y": 0.75},
        {
            "xlabel": "Number of Variables",
            "ylabel": "Feasibility Ratio",
            "title": "Feasibility Ratio vs Model Size",
            "hue": "algorithm",
            "hline": 1.0,
            "hline_label": "Upper Limit (1.0)",
        },
        id="feasibility_ratio_vs_var_number",
    ),
]


def _benchmark_results_with_one_model() -> MagicMock:
    """Build a container reporting a single model with a known variable count."""
    features = MagicMock(spec=FeatureResultContainer)
    features.first.return_value = VarNumberFeatureResult(var_number=VAR_NUMBER)

    benchmark_results = MagicMock(spec=BenchmarkResultContainer)
    benchmark_results.features = {"model_a": features}
    return benchmark_results


class TestAnalysisPlotRun:
    """Each analysis plot pairs a metric with the variable count and delegates to `create`."""

    @pytest.mark.parametrize(("plot_cls", "metric_cls", "metric_result", "expected_row", "expected_kwargs"), RUN_CASES)
    def test_run_builds_rows_and_calls_create(
        self,
        plot_cls: type[BasePlot],
        metric_cls: type[BaseMetric[Any]],
        metric_result: MetricResult,
        expected_row: dict[str, Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        benchmark_results = _benchmark_results_with_one_model()
        benchmark_results.get_all_metrics_of_type.return_value = [("model_a", "algo_1", metric_result)]

        with patch.object(plot_cls, "create") as mock_create:
            plot_cls().run(benchmark_results, save_dir="out")

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(metric_cls)
        mock_create.assert_called_once_with(save_dir="out", rows=[expected_row], **expected_kwargs)

    @pytest.mark.parametrize(("plot_cls", "metric_cls", "metric_result", "expected_row", "expected_kwargs"), RUN_CASES)
    def test_run_with_no_metric_results_passes_empty_rows(
        self,
        plot_cls: type[BasePlot],
        metric_cls: type[BaseMetric[Any]],
        metric_result: MetricResult,
        expected_row: dict[str, Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        _ = metric_result, expected_row
        benchmark_results = _benchmark_results_with_one_model()
        benchmark_results.get_all_metrics_of_type.return_value = []

        with patch.object(plot_cls, "create") as mock_create:
            plot_cls().run(benchmark_results, save_dir=None)

        benchmark_results.get_all_metrics_of_type.assert_called_once_with(metric_cls)
        mock_create.assert_called_once_with(save_dir=None, rows=[], **expected_kwargs)


class TestVarNumberBarChartPlotRun:
    """The property plot reads only features, one row per model."""

    def test_run_builds_one_row_per_model(self) -> None:
        benchmark_results = _benchmark_results_with_one_model()

        with patch.object(VarNumberBarChartPlot, "create") as mock_create:
            VarNumberBarChartPlot().run(benchmark_results, save_dir="out")

        benchmark_results.features["model_a"].first.assert_called_once_with(VarNumberFeature)
        mock_create.assert_called_once_with(
            save_dir="out",
            rows=[{"model": "model_a", "var_number": VAR_NUMBER}],
            x="model",
            y="var_number",
            xlabel="Model",
            ylabel="Number of Variables",
            title="Variables per Model",
            aggregation=Aggregation.MEAN,
            errorbar=AUTO_ERRORBAR,
            hline=None,
            hline_label=None,
            baseline=None,
            ylim=None,
        )

    def test_run_with_no_models_passes_empty_rows(self) -> None:
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.features = {}

        with patch.object(VarNumberBarChartPlot, "create") as mock_create:
            VarNumberBarChartPlot().run(benchmark_results, save_dir=None)

        assert mock_create.call_args.kwargs["rows"] == []
