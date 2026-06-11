"""Tests for PlotsRunUcImpl use case."""

from typing import Any
from unittest.mock import MagicMock, patch

from returns.result import Failure, Success

from luna_bench._internal.usecases.benchmark.plot.plot_run import PlotsRunUcImpl
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
from luna_bench.entities import PlotEntity
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_plot_missing_error import RunPlotMissingError


class TestPlotsRunUcImpl:
    """Test PlotsRunUcImpl use case with real implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.use_case = PlotsRunUcImpl()

    def create_mock_benchmark(
        self, plots: list[Any] | None = None, modelset: MagicMock | None = None, algorithms: list[Any] | None = None
    ) -> MagicMock:
        """Create a mock benchmark entity for testing."""
        if modelset is None:
            model1 = MagicMock()
            model1.name = "model1"
            modelset = MagicMock()
            modelset.models = [model1]

        if algorithms is None:
            algo1 = MagicMock()
            algo1.name = "algo1"
            algorithms = [algo1]

        if plots is None:
            plots = []

        benchmark = MagicMock()
        benchmark.name = "test_benchmark"
        benchmark.modelset = modelset
        benchmark.algorithms = algorithms
        benchmark.plots = plots
        benchmark.data_dir_plots = None
        return benchmark

    def create_mock_plot(
        self,
        name: str = "test_plot",
        required_features: list[Any] | None = None,
        required_metrics: list[Any] | None = None,
    ) -> MagicMock:
        """Create mock plot entity for testing."""
        plot = MagicMock()
        plot.name = name
        plot.required_features = required_features or []
        plot.required_metrics = required_metrics or []
        plot.run = MagicMock()

        plot_entity = MagicMock(spec=PlotEntity)
        plot_entity.name = name
        plot_entity.plot = plot
        return plot_entity

    def test_call_with_no_plots(self) -> None:
        """Test calling use case with no plots to run."""
        benchmark = self.create_mock_benchmark(plots=[])

        result = self.use_case(benchmark)

        assert result == Success(None)

    def test_call_with_single_plot_success(self) -> None:
        """Test calling use case with a single successful plot."""
        plot_entity = self.create_mock_plot()
        benchmark = self.create_mock_benchmark(plots=[plot_entity])

        with patch.object(self.use_case, "_run_plot", return_value=Success(None)):
            result = self.use_case(benchmark)

        assert result == Success(None)

    def test_call_with_specific_plot(self) -> None:
        """Test calling use case with a specific plot parameter."""
        plot1 = self.create_mock_plot(name="plot1")
        plot2 = self.create_mock_plot(name="plot2")
        benchmark = self.create_mock_benchmark(plots=[plot1, plot2])

        # When specific plot is passed, it should return Success
        with patch.object(self.use_case, "_run_plot", return_value=Success(None)):
            result = self.use_case(benchmark, plot=plot1)

        assert result == Success(None)

    def test_call_with_plot_not_in_benchmark(self) -> None:
        """Test calling with plot not in the benchmark returns an error."""
        plot1 = self.create_mock_plot(name="plot1")
        plot2 = self.create_mock_plot(name="plot2")
        benchmark = self.create_mock_benchmark(plots=[plot1])

        result = self.use_case(benchmark, plot=plot2)

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), RunPlotMissingError)

    def test_call_with_multiple_plots(self) -> None:
        """Test calling use case with multiple plots."""
        plot1 = self.create_mock_plot(name="plot1")
        plot2 = self.create_mock_plot(name="plot2")
        benchmark = self.create_mock_benchmark(plots=[plot1, plot2])

        # When multiple plots exist, call should return Success
        with patch.object(self.use_case, "_run_plot", return_value=Success(None)):
            result = self.use_case(benchmark)

        assert result == Success(None)

    def test_run_plot_with_missing_modelset(self) -> None:
        """Test _run_plot when modelset is None."""
        plot_entity = self.create_mock_plot()
        benchmark = self.create_mock_benchmark(plots=[plot_entity], modelset=None)

        with patch.object(self.use_case._logger, "warning"):
            result = self.use_case._run_plot(plot_entity, benchmark)

        assert result == Success(None)

    def test_run_plot_with_feature_failure(self) -> None:
        """Test _run_plot when feature building fails."""
        plot_entity = self.create_mock_plot(required_features=["feature1"])
        benchmark = self.create_mock_benchmark(plots=[plot_entity])

        feature_error = RunFeatureMissingError("feature1", "model1")
        with patch("luna_bench._internal.usecases.benchmark.plot.plot_run.FeatureResultBuilder") as mock_builder:
            mock_builder.return_value.results.return_value = Failure(feature_error)
            result = self.use_case._run_plot(plot_entity, benchmark)

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), RunFeatureMissingError)

    def test_run_plot_with_empty_models_list(self) -> None:
        """Test _run_plot with empty models list."""
        modelset = MagicMock()
        modelset.models = []

        plot_entity = self.create_mock_plot()
        benchmark = self.create_mock_benchmark(plots=[plot_entity], modelset=modelset)

        result = self.use_case._run_plot(plot_entity, benchmark)

        assert result == Success(None)

    def test_run_plot_with_successful_features(self) -> None:
        """Test _run_plot when feature building succeeds (covers features[m.name] = f.unwrap())."""
        plot_entity = self.create_mock_plot(required_features=["feature1"])
        benchmark = self.create_mock_benchmark(plots=[plot_entity])

        feature_container = FeatureResultContainer(data={})

        with (
            patch("luna_bench._internal.usecases.benchmark.plot.plot_run.FeatureResultBuilder") as mock_builder,
            patch.object(self.use_case._logger, "warning"),
        ):
            mock_builder.return_value.results.return_value = Success(feature_container)
            result = self.use_case._run_plot(plot_entity, benchmark)

        assert result == Success(None)
        mock_builder.return_value.results.assert_called_once_with("model1", ["feature1"])

    def test_run_plot_with_successful_metrics(self) -> None:
        """Test _run_plot when all metrics build successfully."""
        plot_entity = self.create_mock_plot(required_metrics=["metric1"])
        benchmark = self.create_mock_benchmark(plots=[plot_entity])

        metric_container = MetricResultContainer(data={})

        with (
            patch("luna_bench._internal.usecases.benchmark.plot.plot_run.MetricResultBuilder") as mock_builder,
            patch.object(self.use_case._logger, "warning"),
        ):
            mock_builder.return_value.results.return_value = Success(metric_container)
            result = self.use_case._run_plot(plot_entity, benchmark)

        assert result == Success(None)
        mock_builder.return_value.results.assert_called_once_with("model1", "algo1", ["metric1"])

    def test_run_plot_with_metric_failure_skips_algorithm(self) -> None:
        """Test _run_plot logs a warning and continues when a metric fails for one algorithm."""
        plot_entity = self.create_mock_plot(required_metrics=["metric1"])
        algo_ok = MagicMock()
        algo_ok.name = "algo_ok"
        algo_fail = MagicMock()
        algo_fail.name = "algo_fail"
        benchmark = self.create_mock_benchmark(plots=[plot_entity], algorithms=[algo_ok, algo_fail])

        metric_container = MetricResultContainer(data={})

        with (
            patch("luna_bench._internal.usecases.benchmark.plot.plot_run.MetricResultBuilder") as mock_builder,
            patch.object(self.use_case._logger, "warning") as mock_logger,
        ):
            # algo_ok succeeds, algo_fail fails
            def side_effect(model: str, algo: str, metrics: list[str]) -> Failure[Any] | Success[Any]:  # noqa: ARG001
                if algo == "algo_fail":
                    return Failure(RunMetricMissingError("metric1", model))
                return Success(metric_container)

            mock_builder.return_value.results.side_effect = side_effect
            result = self.use_case._run_plot(plot_entity, benchmark)

        assert result == Success(None)
        assert any("algo_fail" in str(call) for call in mock_logger.call_args_list)
