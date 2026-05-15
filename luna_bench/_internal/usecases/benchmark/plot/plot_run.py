from typing import TYPE_CHECKING

from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.benchmark.helper import FeatureResultBuilder, MetricResultBuilder
from luna_bench._internal.usecases.benchmark.protocols import PlotsRunUc
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.entities import PlotEntity
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.errors.run_errors.plots_errors.plot_exectuion_error import PlotExecutionError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_plot_missing_error import RunPlotMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
    from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
    from luna_bench.custom.types import AlgorithmName, ModelName


class PlotsRunUcImpl(PlotsRunUc):
    """
    Use case implementation for validating and executing benchmark plots.

    This class orchestrates the execution of all plots defined in a benchmark,
    handling validation and execution errors according to the configured mode.

    Notes
    -----
    Plot execution is sequential and order-dependent based on the benchmark
    configuration. Each plot is validated before execution.
    """

    def __init__(
        self,
    ) -> None:
        self._logger = Logging.get_logger(__name__)

    def _run_plot(
        self, plot_entity: PlotEntity, benchmark: BenchmarkEntity
    ) -> Result[None, RunFeatureMissingError | RunMetricMissingError | PlotExecutionError]:
        features: dict[ModelName, FeatureResultContainer] = {}
        metrics: dict[ModelName, dict[AlgorithmName, MetricResultContainer]] = {}
        if benchmark.modelset is None:
            self._logger.warning(f"Modelset is missing for benchmark '{benchmark.name}'")
            return Success(None)

        for m in benchmark.modelset.models:
            if plot_entity.plot.required_features:
                f = FeatureResultBuilder(benchmark).results(m.name, plot_entity.plot.required_features)
                if not is_successful(f):
                    return Failure(f.failure())
                features[m.name] = f.unwrap()

            if plot_entity.plot.required_metrics:
                metrics[m.name] = {}
                for a in benchmark.algorithms:
                    me = MetricResultBuilder(benchmark).results(m.name, a.name, plot_entity.plot.required_metrics)
                    if not is_successful(me):
                        return Failure(me.failure())

                    metrics[m.name][a.name] = me.unwrap()

        benchmark_result: BenchmarkResultContainer = BenchmarkResultContainer(
            features=features,
            metrics=metrics,
        )
        try:
            plot_entity.plot.run(benchmark_result)
        except Exception as e:
            self._logger.warning(f"Error running plot {plot_entity.name}: {e}")
            return Failure(PlotExecutionError(plot_entity.name, benchmark.name, e))
        return Success(None)

    def __call__(
        self,
        benchmark: BenchmarkEntity,
        plot: PlotEntity | None = None,
    ) -> Result[
        None,
        RunFeatureMissingError | RunPlotMissingError | PlotRunError | UnknownLunaBenchError | RunMetricMissingError,
    ]:
        """
        Execute all plots defined in the benchmark.

        This method iterates through all plots in the benchmark, validates each
        plot against the benchmark data, and executes the plot generation if
        validation succeeds.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing plots to execute and the data (metrics,
            features, algorithms, models) required for plot generation.

        Returns
        -------
        Result[None, PlotRunError | UnknownLunaBenchError]
            Success(None) if all plots executed successfully (or if errors were
            handled gracefully in CONTINUE_ON_ERROR mode). Failure with PlotRunError
            if validation fails, or UnknownLunaBenchError if execution raises an
            exception (only in FAIL_ON_ERROR mode).

        Notes
        -----
        - In FAIL_ON_ERROR mode: Returns Failure on first validation or execution error
        - In CONTINUE_ON_ERROR mode: Logs warnings and continues with remaining plots
        - Validation is performed before execution for each plot
        - Plot execution order follows the order defined in the benchmark
        """
        plots: list[PlotEntity]
        if plot is not None:
            # Check if the feature is part of the benchmark
            if plot not in benchmark.plots:
                return Failure(RunPlotMissingError(plot.name, benchmark.name))
            plots = [plot]
        else:
            plots = benchmark.plots

        for p in plots:
            r = self._run_plot(p, benchmark)
            if not is_successful(r):
                self._logger.warning(f"Error running plot {p.name}: {r.failure()}")

        return Success(None)
