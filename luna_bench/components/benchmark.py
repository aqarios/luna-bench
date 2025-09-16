from __future__ import annotations

from logging import Logger
from typing import ClassVar

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Result

from luna_bench import UsecaseContainer
from luna_bench._internal.domain_models import (
    AlgorithmConfigDomain,
    MetricConfigDomain,
    ModelmetricConfigDomain,
    PlotConfigDomain,
)
from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
from luna_bench._internal.usecases.benchmark.protocols import (
    BenchmarkAddAlgorithmUc,
    BenchmarkAddMetricUc,
    BenchmarkAddModelMetricUc,
    BenchmarkAddPlotUc,
    BenchmarkCreateUc,
    BenchmarkLoadAllUc,
    BenchmarkLoadUc,
    BenchmarkRemoveMetricUc,
    BenchmarkRemoveModelMetricUc,
    BenchmarkRemovePlotUc,
)
from luna_bench.components.algorithm import Algorithm
from luna_bench.components.metric import Metric
from luna_bench.components.model_metric import ModelMetric
from luna_bench.components.model_set import ModelSet
from luna_bench.components.plot import Plot
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class Benchmark(BaseModel):
    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    name: str
    modelset: ModelSet | None

    model_metrics: list[ModelMetric]
    metrics: list[Metric]
    algorithms: list[Algorithm]
    plots: list[Plot]

    @staticmethod
    @inject
    def create(
        name: str, benchmark_create: BenchmarkCreateUc = Provide[UsecaseContainer.benchmark_create_uc]
    ) -> Benchmark:
        """
        Create a new benchmark instance with the specified name.

        This factory method creates a Benchmark object ready for configuration. The name will be used as the ID.

        Args:
            name (str): Name for the benchmark. Will serve as ID.
            benchmark_create (BenchmarkCreateUc): Injected use case for benchmark creation.

        Returns:
            Benchmark: A newly created benchmark instance.

        Example:
            >>> benchmark = Benchmark.create("PortfolioOptimization_Comparison_2025")
            >>> print(benchmark.name)
            'PortfolioOptimization_Comparison_2025'
        """
        result: Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError] = benchmark_create(name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to create benchmark: {error}")
            raise RuntimeError(error)

        success: BenchmarkDomain = result.unwrap()
        return Benchmark._to_benchmark(success)

    @staticmethod
    def import_from_file(file_path: str) -> Benchmark:
        """
        Import a benchmark configuration from a file.

        Loads a previously exported benchmark configuration from a file, including
        all algorithms, metrics, plots, and settings.

        Args:
            file_path (str): Path to the benchmark configuration file. Todo What will be the format?

        Returns:
            Benchmark: A benchmark instance loaded from the file.

        Example:
            >>> benchmark = Benchmark.import_from_file("/path/to/benchmark.extension")
        """
        ...

    def delete(self) -> None:
        """
        Permanently delete this benchmark and all associated data.

        This method removes the benchmark from persistent / cloud storage, including all
        configuration, results, and generated plots. This operation cannot be undone.

        Warning:
            This is a destructive operation. All benchmark data will be lost.

        Example:
            >>> benchmark.delete()
            # Benchmark and all its data are now permanently deleted
        """
        ...

    @staticmethod
    @inject
    def load(name: str, benchmark_load: BenchmarkLoadUc = Provide[UsecaseContainer.benchmark_load_uc]) -> Benchmark:
        """
        Load an existing benchmark by name from persistent / cloud storage.

        Retrieves a previously created benchmark with all its configurations,
        including algorithms, metrics, plots, and any existing results.

        Args:
            name (str): Name of the benchmark to load.
            benchmark_load (BenchmarkLoadUc): Todo

        Returns:
            Benchmark: The loaded benchmark instance with all configurations.


        Example:
            >>> benchmark = Benchmark.load("my_existing_benchmark")
        """
        result: Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError] = benchmark_load(name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to load benchmark: {error}")
            raise RuntimeError(error)

        success: BenchmarkDomain = result.unwrap()
        return Benchmark._to_benchmark(success)

    @staticmethod
    @inject
    def load_all(
        benchmark_load_all: BenchmarkLoadAllUc = Provide[UsecaseContainer.benchmark_load_all_uc],
    ) -> list[Benchmark]:
        """
        Load all existing benchmarks from persistent storage.

        Retrieves all benchmarks that have been created and stored locally / cloud.
        Useful for getting an overview of all available benchmarks or for batch
        operations across multiple benchmarks, e.g. to add a new metric.

        Args:
            benchmark_load_all (BenchmarkLoadAllUc): Injected use case for loading all benchmarks.

        Returns:
            list[Benchmark]: List of all benchmark instances in the system.

        Example:
            >>> all_benchmarks = Benchmark.load_all()
            >>> print(f"Found {len(all_benchmarks)} benchmarks")
            Found 5 benchmarks
        """
        result: Result[list[BenchmarkDomain], UnknownLunaBenchError] = benchmark_load_all()
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to load all benchmarks: {error}")
            raise RuntimeError(error)
        success: list[BenchmarkDomain] = result.unwrap()
        return [Benchmark._to_benchmark(b) for b in success]

    def run(self) -> None:
        """
        Execute the complete benchmark evaluation process.

        Runs all configured algorithms against the modelset using all specified
        metrics and generates all configured plots. This is the main execution
        method that orchestrates the entire benchmarking workflow.

        The execution includes:
        - Running all algorithms on the modelset
        - Computing all metrics and model metrics
        - Generating all visualization plots
        - Storing results for later analysis

        Example:
            >>> benchmark.run()
            # All algorithms executed, metrics computed, plots generated
        """
        ...

    def reset(self) -> None:
        """
        Reset the benchmark to its initial state, clearing all results.

        Removes all execution results, computed metrics, and generated plots
        while preserving the benchmark configuration (algorithms, metrics, plots).
        This allows for a clean re-run of the benchmark.

        Example:
            >>> benchmark.reset()
            # Results cleared, configuration preserved
            >>> benchmark.run()  # Fresh execution
        """
        ...

    def export_to_file(self, file_path: str) -> None:
        """
        Export the benchmark configuration to a file.

        Saves the complete benchmark configuration including algorithms, metrics,
        plots, and settings to a file. The exported file can later be imported
        using import_from_file() to recreate the benchmark. Todo what is the format of the file?

        Args:
            file_path (str): Path where the benchmark configuration will be saved.

        Example:
            >>> benchmark.export_to_file("/path/to/my_benchmark")
            # Benchmark configuration saved to file
        """
        ...

    # @property
    # def modelset(self) -> ModelSet: ...
    #
    # @modelset.setter
    # def modelset(self, value: ModelSet) -> None: ...

    @inject
    def add_model_metric(
        self,
        model_metric: ModelMetric,
        benchmark_add_modelmetric: BenchmarkAddModelMetricUc = Provide[UsecaseContainer.benchmark_add_modelmetric_uc],
    ) -> None:
        """
        Add a model-specific metric to the benchmark.

        Model metrics are specialized evaluation measures that assess specific
        properties of the models being benchmarked, such as primal / dual bounds or rhs ranges.

        Args:
            model_metric (ModelMetric): The model metric to add to the benchmark.
            benchmark_add_modelmetric (BenchmarkAddModelMetricUc): Injected use case.

        Example:
            >>> from luna_bench.metrics import PrimalBound
            >>> p_bound = ModelMetric(name="p_bound", metric=PrimalBound())
            >>> benchmark.add_model_metric(p_bound)
        """
        result: Result[ModelmetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
            benchmark_add_modelmetric(self.name, model_metric.name, model_metric._to_domain_config())
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add model metric to benchmark: {error}")
            raise RuntimeError(error)
        success: ModelmetricConfigDomain = result.unwrap()
        self.model_metrics.append(ModelMetric._from_domain(success))

    @inject
    def remove_model_metric(
        self,
        model_metric: ModelMetric | str,
        benchmark_remove_modelmetric: BenchmarkRemoveModelMetricUc = Provide[
            UsecaseContainer.benchmark_remove_modelmetric_uc
        ],
    ) -> None:
        """
        Remove a model metric from the benchmark.

        Removes the specified model metric from the benchmark configuration.
        The metric can be specified either by ModelMetric object or by name string.

        Args:
            model_metric (ModelMetric | str): The model metric to remove, either as
                an object or by name.
            benchmark_remove_modelmetric (BenchmarkRemoveModelMetricUc): Injected use case.

        Example:
            >>> from luna_bench.metrics import PrimalBound
            >>> benchmark.remove_model_metric("p_bound")
            # or
            >>> benchmark.remove_model_metric(PrimalBound())
        """

        model_metric_name = model_metric.name if isinstance(model_metric, ModelMetric) else model_metric

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_modelmetric(
            self.name, model_metric_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add model metric to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.model_metrics, model_metric_name)

    @inject
    def add_metric(
        self,
        metric: Metric,
        benchmark_add_metric_uc: BenchmarkAddMetricUc = Provide[UsecaseContainer.benchmark_add_metric_uc],
    ) -> None:
        """
        Add an evaluation metric to the benchmark.

        General metrics evaluate algorithm performance and execution characteristics
        such as runtime, memory usage, convergence properties, or solution quality.

        Args:
            metric (Metric): The metric to add to the benchmark.
            benchmark_add_metric_uc (BenchmarkAddMetricUc): Injected use case.


        Example:
            >>> from luna_bench.metrics import TimeToSolution
            >>> runtime_metric = Metric(name="tts", metric=TimeToSolution())
            >>> benchmark.add_metric(runtime_metric)
        """
        result: Result[MetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
            benchmark_add_metric_uc(self.name, metric.name, metric._to_domain_config())
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add metric to benchmark: {error}")
            raise RuntimeError(error)
        success: MetricConfigDomain = result.unwrap()
        self.metrics.append(Metric._from_domain(success))

    @inject
    def remove_metric(
        self,
        metric: Metric | str,
        benchmark_remove_metric: BenchmarkRemoveMetricUc = Provide[UsecaseContainer.benchmark_remove_metric_uc],
    ) -> None:
        """
        Remove an evaluation metric from the benchmark.

        Removes the specified metric from the benchmark configuration. The metric
        can be specified either by Metric object or by name string.

        Args:
            metric (Metric | str): The metric to remove, either as an object or by name.
            benchmark_remove_metric (BenchmarkRemoveMetricUc): Injected use case.

        Example:
            >>> benchmark.remove_metric("tts")
            # or
            >>> from luna_bench.metrics import TimeToSolution
            >>> benchmark.remove_metric(TimeToSolution())
        """
        metric_name = metric.name if isinstance(metric, Metric) else metric

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_metric(
            self.name, metric_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add metric to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.metrics, metric_name)

    @inject
    def add_algorithm(
        self,
        algorithm: Algorithm,
        benchmark_add_algorithm: BenchmarkAddAlgorithmUc = Provide[UsecaseContainer.benchmark_add_algorithm_uc],
    ) -> None:
        """
        Add an algorithm to the benchmark for evaluation.

        Adds a quantum or classical algorithm to be included in the benchmark
        evaluation. The algorithm will be executed against the configured modelset
        and evaluated using all specified metrics.

        Args:
            algorithm (Algorithm): The algorithm to add to the benchmark.
            benchmark_add_algorithm (BenchmarkAddAlgorithmUc): Injected use case.


        Example:
            >>> from luna_quantum.algorithms import SimulatedAnnealing
            >>> sa_algorithm = Algorithm(name="simulated_annealing", algorithm=SimulatedAnnealing())
            >>> benchmark.add_algorithm(sa_algorithm)
        """
        result: Result[AlgorithmConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
            benchmark_add_algorithm(self.name, algorithm.name,
                                    algorithm._to_domain_algorithm(),
                                    algorithm._to_domain_backend()
                                    )
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
            raise RuntimeError(error)
        success: AlgorithmConfigDomain = result.unwrap()
        self.algorithms.append(Algorithm._from_domain(success))



    def remove_algorithm(self, algorithm: str| Algorithm,
                         benchmark_remove_algorithm: BenchmarkRemoveMetricUc = Provide[UsecaseContainer.benchmark_remove_algorithm_uc] ) -> None:
        """
        Remove an algorithm from the benchmark.

        Removes the specified algorithm from the benchmark configuration. The algorithm
        will no longer be included in benchmark executions. Can be specified either
        by Algorithm object or by name string.

        Args:
            algorithm (str | Algorithm): The algorithm to remove, either as an object
                or by name.
            benchmark_remove_algorithm (BenchmarkRemoveMetricUc): Injected use case.

        Example:
            >>> benchmark.remove_algorithm("simulated_annealing")
            # or
            >>> benchmark.remove_algorithm(sa_algorithm)
        """

        algorithm_name = algorithm.name if isinstance(algorithm, Algorithm) else algorithm

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_algorithm(
            self.name, algorithm_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.algorithms, algorithm_name)

    def add_plot(self, plot: Plot,
        benchmark_add_plot: BenchmarkAddPlotUc = Provide[UsecaseContainer.benchmark_add_plot_uc]
    ) -> None:
        """
        Add a visualization plot to the benchmark.

        Adds a plot configuration that will be generated when the benchmark is
        evaluated. Plots provide visual analysis of the benchmark results, such
        as performance comparisons, or statistical distributions. For example, add a barchart that compares
        a specified metric against each algorithm in the benchmark.

        Args:
            plot (Plot): The plot configuration to add to the benchmark.
            benchmark_add_plot (BenchmarkAddPlotUc): Injected use case.

        Example:
            >>> from luna_bench.plots import BarChart
            >>> bar_chart = Plot(name="performance_comparison", plot=BarChart(title="Algorithm Performance", metric='tts'))
            >>> benchmark.add_plot(bar_chart)
        """
        result: Result[PlotConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
            benchmark_add_plot(self.name, plot.name, plot._to_domain_config())
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add plot to benchmark: {error}")
            raise RuntimeError(error)
        success: PlotConfigDomain = result.unwrap()
        self.plots.append(Plot._from_domain(success))

    def remove_plot(self, plot: str| Plot,
                         benchmark_remove_plot: BenchmarkRemovePlotUc = Provide[UsecaseContainer.benchmark_remove_plot_uc] ) -> None:
        """
        Remove a visualization plot from the benchmark.

        Removes the specified plot from the benchmark configuration. The plot
        will no longer be generated during benchmark evaluation. Can be specified
        either by Plot object or by name string.

        Args:
            plot (str | Plot): The plot to remove, either as an object or by name.
            benchmark_remove_plot (BenchmarkRemovePlotUc): Injected use case.

        Raises:
            RuntimeError: If the plot doesn't exist or removal fails.

        Example:
            >>> benchmark.remove_plot("performance_comparison")
            # or
            >>> benchmark.remove_plot(bar_chart)
        """

        plot_name = plot.name if isinstance(plot, Plot) else plot

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_plot(
            self.name, plot_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove plot to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.plots, plot_name)

    def run_model_metrics(self) -> None:
        """
        Execute only the model metrics evaluation phase.

        Runs all configured model metrics against the modelset without executing
        algorithms or generating plots. Useful for isolated model evaluation or
        when only model-specific metrics are needed. For example, one can use this to get more insights into
        the modelset itself.

        Example:
            >>> benchmark.run_model_metrics()
            # Only model metrics computed, algorithms and plots skipped
        """
        ...
    def run_metrics(self) -> None:
        """
        Execute only the algorithm metrics evaluation phase.

        Runs all configured algorithm metrics without executing algorithms or
        generating plots. Assumes that algorithm execution results are already
        available from a previous run. Todo this raise an error if not all results are available!

        Example:
            >>> benchmark.run_metrics()
            # Only general metrics computed based on existing algorithm results
        """
        ...

    def run_plots(self) -> None:
        """
        Generate only the visualization plots.

        Creates all configured plots based on existing benchmark results without
        re-running algorithms or metrics. Assumes that metric evaluation results
        are already available, todo if not this should raise an error!

        Example:
            >>> benchmark.run_plots()
            # Only plots generated based on existing results
        """
        ...

    def run_jobs(self) -> None:
        """
        Execute the benchmark using a job queue system.

        Submits the benchmark execution to a job queue for distributed or
        asynchronous processing. This is useful for long-running benchmarks
        or when computational resources need to be managed across multiple jobs.

        Example:
            >>> benchmark.run_jobs()
            # Benchmark submitted to job queue for execution
        """
        ...

    def list_model_metrics_classes(self) -> list[None]:
        """
        List the model metrics currently configured in this benchmark.

        Returns a list of the model metric instances that have been added to
        this benchmark and will be executed during benchmark evaluation.

        Returns:
            list[None]: List of configured model metric instances.

        Example:
            >>> benchmark.add_model_metric(PrimalBound())
            >>> configured_metrics = benchmark.list_model_metrics_classes()
            >>> print(f"Configured model metrics: {len(configured_metrics)}")
            Configured model metrics: 1
        """
        ...

    def list_metrics_classes(self) -> list[None]:
        """
        List the evaluation metrics currently configured in this benchmark.

        Returns a list of the metric instances that have been added to this
        benchmark and will be executed during benchmark evaluation.

        Returns:
            list[None]: List of configured metric instances.

        Example:
            >>> benchmark.add_metric(TimeToSolution())
            >>> configured_metrics = benchmark.list_metrics_classes()
            >>> print(f"Configured metrics: {len(configured_metrics)}")
            Configured metrics: 1
        """
        ...

    def list_plots_classes(self) -> list[None]:
        """
        List the plots currently configured in this benchmark.

        Returns a list of the plot instances that have been added to this
        benchmark and will be generated during benchmark evaluation.

        Returns:
            list[None]: List of configured plot instances.

        Example:
            >>> benchmark.add_plot(bar_chart_plot)
            >>> configured_plots = benchmark.list_plots_classes()
            >>> print(f"Configured plots: {len(configured_plots)}")
            Configured plots: 1
        """
        ...

    def list_algorithms(self) -> list[None]:
        """
        List the algorithms currently configured in this benchmark.

        Returns a list of the algorithm instances that have been added to this
        benchmark and will be executed during benchmark evaluation.

        Returns:
            list[None]: List of configured algorithm instances.

        Example:
            >>> benchmark.add_algorithm(sa_algorithm)
            >>> configured_algorithms = benchmark.list_algorithms()
            >>> print(f"Configured algorithms: {len(configured_algorithms)}")
            Configured algorithms: 1
        """
        ...

    def list_backends(self) -> list[None]:
        """
        List the execution backends used by configured algorithms.

        Returns a list of the backend instances that are being used by the
        algorithms configured in this benchmark for execution.

        Returns:
            list[None]: List of backend instances used by configured algorithms.

        Example:
            >>> configured_backends = benchmark.list_backends()
            >>> print(f"Backends in use: {len(configured_backends)}")
            Backends in use: 2
        """
        ...

    @staticmethod
    def _to_benchmark(benchmark: BenchmarkDomain) -> Benchmark:
        return Benchmark(
            name=benchmark.name,
            modelset=ModelSet._to_data_set(benchmark.modelset) if benchmark.modelset else None,
            model_metrics=[ModelMetric._from_domain(m) for m in benchmark.modelmetrics],
            metrics=[Metric._from_domain(m) for m in benchmark.metrics],
            algorithms=[Algorithm._from_domain(a) for a in benchmark.algorithms],
            plots=[Plot._from_domain(p) for p in benchmark.plots],
        )

    @staticmethod
    def _update(old_benchmark: Benchmark, new_benchmark: BenchmarkDomain) -> Benchmark:
        # TODO call update methods of each component instead of overwriting
        old_benchmark.name = new_benchmark.name
        old_benchmark.modelset = ModelSet._to_data_set(new_benchmark.modelset) if new_benchmark.modelset else None

        # TODO remove no longer present thing, add new ones, update existing ones
        old_benchmark.model_metrics = []
        old_benchmark.metrics = []
        old_benchmark.algorithms = []
        old_benchmark.plots = []
        return old_benchmark

    @staticmethod
    def _remove_name_from_list(obj_list: list[BaseModel], name: str) -> None:
        for i, obj in enumerate(obj_list):
            if getattr(obj, "name", None) == name:
                del obj_list[i]
                return  # since we use name as a unique identifier, we can break after the first match (only one name per list allowed).
