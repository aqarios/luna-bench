from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.custom import BaseFeature, BaseMetric, BasePlot
from luna_bench.custom.base_results.feature_result import FeatureResult
from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.decorators.plot import plot

if TYPE_CHECKING:
    from luna_model import Model, Solution

    from luna_bench._internal.registries import Registry
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class MockPlotFeature(BaseFeature[FeatureResult]):
    def run(self, model: Model) -> FeatureResult:
        raise NotImplementedError


class MockPlotMetric(BaseMetric[MetricResult]):
    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> MetricResult:
        raise NotImplementedError


class TestPlotDecorator:
    @pytest.fixture()
    def plot_registry(self) -> Registry[BasePlot]:
        return ArbitraryDataRegistry[BasePlot](kind="plot")

    @pytest.mark.parametrize(
        ("plot_id", "expected_in_registry"),
        [
            (None, "test_plot"),
            ("custom.plot_id", "custom.plot_id"),
        ],
        ids=["default_id", "custom_id"],
    )
    def test_plot_class_registration(
        self,
        plot_registry: Registry[BasePlot],
        plot_id: str | None,
        expected_in_registry: str,
    ) -> None:
        @plot(plot_id=plot_id, plot_registry=plot_registry)
        class TestPlot(BasePlot):
            def run(self, benchmark_results: BenchmarkResultContainer) -> None:
                _ = benchmark_results

        assert isinstance(TestPlot, type)
        assert issubclass(TestPlot, BasePlot)
        assert any(expected_in_registry in r_id for r_id in plot_registry.ids())

    def test_plot_function_registration(self, plot_registry: Registry[BasePlot]) -> None:
        @plot(plot_registry=plot_registry)
        def my_test_plot(benchmark_results: BenchmarkResultContainer) -> None:
            _ = benchmark_results

        assert isinstance(my_test_plot, type)
        assert issubclass(my_test_plot, BasePlot)
        assert any("my_test_plot" in r_id for r_id in plot_registry.ids())

    def test_plot_function_execution(self) -> None:
        @plot
        def executable_plot(benchmark_results: BenchmarkResultContainer) -> None:
            _ = benchmark_results

        plot_inst = executable_plot()
        result = plot_inst.run(cast("BenchmarkResultContainer", {}))
        assert result is None

    def test_plot_preserves_function_metadata(self) -> None:
        @plot
        def documented_plot(benchmark_results: BenchmarkResultContainer) -> None:
            """Run this."""
            _ = benchmark_results

        assert documented_plot.__doc__ == "Run this."
        assert documented_plot.__name__ == "documented_plot"

    @pytest.mark.parametrize(
        ("required_components", "expected_features", "expected_metrics"),
        [
            (None, [], []),
            (MockPlotFeature, [MockPlotFeature], []),
            (MockPlotMetric, [], [MockPlotMetric]),
            ([MockPlotFeature], [MockPlotFeature], []),
            ((MockPlotMetric,), [], [MockPlotMetric]),
        ],
        ids=["none", "single_feature", "single_metric", "list_feature", "tuple_metric"],
    )
    def test_plot_required_components(
        self,
        plot_registry: Registry[BasePlot],
        required_components: type[BaseFeature | BaseMetric]
        | None
        | list[type[BaseFeature | BaseMetric]]
        | tuple[type[BaseFeature | BaseMetric], ...],
        expected_features: list[type[BaseFeature]],
        expected_metrics: list[type[BaseMetric]],
    ) -> None:
        @plot(required_components, plot_registry=plot_registry)
        class TestComponentPlot(BasePlot):
            def run(self, benchmark_results: BenchmarkResultContainer) -> None:
                _ = benchmark_results

        assert TestComponentPlot.required_features == expected_features
        assert TestComponentPlot.required_metrics == expected_metrics

    def test_plot_required_components_mixed(
        self,
        plot_registry: Registry[BasePlot],
    ) -> None:
        @plot(required_components=[MockPlotFeature, MockPlotMetric], plot_registry=plot_registry)
        class MixedPlot(BasePlot):
            def run(self, benchmark_results: BenchmarkResultContainer) -> None:
                _ = benchmark_results

        assert MixedPlot.required_features == [MockPlotFeature]
        assert MixedPlot.required_metrics == [MockPlotMetric]

    def test_plot_required_components_single(
        self,
        plot_registry: Registry[BasePlot],
    ) -> None:
        @plot(required_components=MockPlotMetric, plot_registry=plot_registry)
        class SingleMetricPlot(BasePlot):
            def run(self, benchmark_results: BenchmarkResultContainer) -> None:
                _ = benchmark_results

        assert SingleMetricPlot.required_features == []
        assert SingleMetricPlot.required_metrics == [MockPlotMetric]

    def test_plot_list_as_first_positional_arg(
        self,
        plot_registry: Registry[BasePlot],
    ) -> None:
        @plot([MockPlotFeature, MockPlotMetric], plot_registry=plot_registry)
        class ListArgPlot(BasePlot):
            def run(self, benchmark_results: BenchmarkResultContainer) -> None:
                _ = benchmark_results

        assert ListArgPlot.required_features == [MockPlotFeature]
        assert ListArgPlot.required_metrics == [MockPlotMetric]
