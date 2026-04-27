from typing import TYPE_CHECKING

from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.benchmark.helper import FeatureResultBuilder, MetricResultBuilder
from luna_bench._internal.usecases.benchmark.protocols import PlotsRunUc
from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.entities import PlotEntity
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.run_errors.run_plot_missing_error import RunPlotMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench.base_components.data_types.feature_results import FeatureResults
    from luna_bench.base_components.data_types.metric_results import MetricResults
    from luna_bench.types import AlgorithmName, ModelName


class PlotsRunUcImpl(PlotsRunUc):
    """
    Use case implementation for validating and executing benchmark plots.

    This class orchestrates the execution of all plots defined in a benchmark,
    handling validation and execution errors according to the configured mode.

    Parameters
    ----------
    error_handling_mode : UseCaseErrorHandlingMode, optional
        Determines behavior when plot validation or execution fails.
        - FAIL_ON_ERROR: Stop on first error and return Failure
        - CONTINUE_ON_ERROR: Log warning and continue with remaining plots
        Default is FAIL_ON_ERROR.

    Attributes
    ----------
    error_handling_mode : UseCaseErrorHandlingMode
        The configured error handling strategy.

    Notes
    -----
    Plot execution is sequential and order-dependent based on the benchmark
    configuration. Each plot is validated before execution.
    """

    def __init__(
        self,
    ) -> None:
        self._logger = Logging.get_logger(__name__)

    def __call__(
        self,
        benchmark: BenchmarkEntity,
        plot: PlotEntity | None = None,
    ) -> Result[None, PlotRunError | UnknownLunaBenchError]:
        """
        Execute all plots defined in the benchmark.

        This method iterates through all plots in the benchmark, validates each
        plot against the benchmark data, and executes the plot generation if
        validation succeeds. Error handling behavior depends on the configured
        error_handling_mode.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing plots to execute and the data (metrics,
            features, algorithms, models) required for plot generation.
        error_handling_mode : UseCaseErrorHandlingMode, optional
            Error handling strategy for plot validation and execution failures.
            Default is FAIL_ON_ERROR.

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
            features: dict[ModelName, FeatureResults] = {}
            metrics: dict[ModelName, dict[AlgorithmName, MetricResults]] = {}

            for m in benchmark.modelset.models:
                if p.plot.required_features:
                    f = FeatureResultBuilder(benchmark).results(m.name, p.plot.required_features)
                    if not is_successful(f):
                        return Failure(f.failure())
                    features[m.name] = f.unwrap()

                if p.plot.required_metrics:
                    metrics[m.name] = {}
                    for a in benchmark.algorithms:
                        me = MetricResultBuilder(benchmark).results(m.name, a.name, p.plot.required_metrics)
                        if not is_successful(me):
                            return Failure(me.failure())

                        metrics[m.name][a.name] = me.unwrap()

            benchmark_result: BenchmarkResults = BenchmarkResults(
                features=features,
                metrics=metrics,
            )
            try:
                p.plot.run(benchmark_result)
            except Exception as e:
                self._logger.warning(f"Error running plot {p.name}: {e}")

        return Success(None)
