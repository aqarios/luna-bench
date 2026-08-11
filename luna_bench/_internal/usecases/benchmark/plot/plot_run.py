from typing import TYPE_CHECKING

from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.benchmark.helper import FeatureResultBuilder, MetricResultBuilder
from luna_bench._internal.usecases.benchmark.protocols import PlotsRunUc
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.entities import PlotEntity
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.errors.run_errors.plots_errors.plot_exectuion_error import PlotExecutionError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_plot_missing_error import RunPlotMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
    from luna_bench.custom.types import AlgorithmName, FeatureClass, ModelName


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
        self._logger = BenchLogger.get_logger(__name__)

    @staticmethod
    def _dimension_features(plot_entity: PlotEntity) -> "list[FeatureClass]":
        """Return the features a plot organises its data by, if any of them is one.

        A dimension can be given to either axis of a plot - the bars or the colours - so
        both are asked. Only a `FeatureDimension` needs a feature; the others read the
        results or the algorithm configurations.

        Parameters
        ----------
        plot_entity : PlotEntity
            The plot about to be drawn.

        Returns
        -------
        list[FeatureClass]
            The features the plot's dimensions look up, without duplicates.
        """
        features: list[FeatureClass] = []
        for name in ("x", "grouping"):
            feature = getattr(getattr(plot_entity.plot, name, None), "feature", None)
            if isinstance(feature, type) and feature not in features:
                features.append(feature)
        return features

    @staticmethod
    def _feature_results(
        builder: FeatureResultBuilder,
        model_name: str,
        required: "list[FeatureClass]",
        dimensions: "list[FeatureClass]",
    ) -> "Result[FeatureResultContainer, RunFeatureMissingError]":
        """Collect the feature results one plot needs for one model.

        The features a plot declares have to be there; the ones its dimensions look up do
        not - a model without one is drawn ungrouped rather than not at all. Which of the
        two a missing result is is the plot's business, so the builder is asked for both
        and only the first failure is passed on.

        Parameters
        ----------
        builder : FeatureResultBuilder
            Builds the results of the benchmark.
        model_name : str
            The model to collect for.
        required : list[FeatureClass]
            The features the plot declared it needs.
        dimensions : list[FeatureClass]
            The features the plot's dimensions look up, if any of them does.

        Returns
        -------
        Result[FeatureResultContainer, RunFeatureMissingError]
            The results, or the failure of a feature the plot cannot do without.
        """
        results = builder.results(model_name, required)
        if not is_successful(results) or not dimensions:
            return results

        organised = builder.results(model_name, dimensions)
        if not is_successful(organised):
            return results

        return Success(
            FeatureResultContainer.model_construct(data={**results.unwrap().data, **organised.unwrap().data})
        )

    def _run_plot(
        self, plot_entity: PlotEntity, benchmark: BenchmarkEntity
    ) -> Result[None, RunFeatureMissingError | RunMetricMissingError | PlotExecutionError]:
        features: dict[ModelName, FeatureResultContainer] = {}
        metrics: dict[ModelName, dict[AlgorithmName, MetricResultContainer]] = {}
        if benchmark.modelset is None:
            self._logger.warning(f"Modelset is missing for benchmark '{benchmark.name}'")
            return Success(None)

        # A plot may organise its data along a feature it does not otherwise need, so
        # those are collected as well - optionally, since a model without one is simply
        # ungrouped rather than unplottable.
        dimension_features = self._dimension_features(plot_entity)

        # Built once rather than per model - each one indexes the whole benchmark - and
        # only when the plot has something to read, so a plot that needs neither touches
        # neither.
        needs_features = bool(plot_entity.plot.required_features or dimension_features)
        feature_builder = FeatureResultBuilder(benchmark) if needs_features else None
        metric_builder = MetricResultBuilder(benchmark) if plot_entity.plot.required_metrics else None

        for m in benchmark.modelset.models:
            if feature_builder is not None:
                f = self._feature_results(
                    feature_builder, m.name, plot_entity.plot.required_features, dimension_features
                )
                if not is_successful(f):
                    return Failure(f.failure())
                features[m.name] = f.unwrap()

            if metric_builder is not None:
                metrics[m.name] = {}
                for a in benchmark.algorithms:
                    me = metric_builder.results(m.name, a.name, plot_entity.plot.required_metrics)
                    if not is_successful(me):
                        self._logger.warning(
                            f"Algorithm '{a.name}' failed on model '{m.name}' "
                            f"and will be skipped for plot '{plot_entity.name}'."
                        )
                        continue

                    metrics[m.name][a.name] = me.unwrap()

        benchmark_result: BenchmarkResultContainer = BenchmarkResultContainer(
            features=features,
            metrics=metrics,
            # The configured algorithm instances, so a plot can read what an algorithm was
            # run with - the layer count of a sweep, say - and not just what it produced.
            algorithms=BenchmarkResultContainer.algorithm_results(benchmark),
        )
        try:
            plot_entity.plot.run(benchmark_result, save_dir=benchmark.data_dir_plots)
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
