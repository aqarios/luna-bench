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
        result: Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError] = benchmark_create(name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to create benchmark: {error}")
            raise RuntimeError(error)

        success: BenchmarkDomain = result.unwrap()
        return Benchmark._to_benchmark(success)

    @staticmethod
    def import_from_file(file_path: str) -> Benchmark: ...

    def delete(self) -> None: ...

    @staticmethod
    @inject
    def load(name: str, benchmark_load: BenchmarkLoadUc = Provide[UsecaseContainer.benchmark_load_uc]) -> Benchmark:
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
        result: Result[list[BenchmarkDomain], UnknownLunaBenchError] = benchmark_load_all()
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to load all benchmarks: {error}")
            raise RuntimeError(error)
        success: list[BenchmarkDomain] = result.unwrap()
        return [Benchmark._to_benchmark(b) for b in success]

    def run(self) -> None: ...

    def reset(self) -> None: ...

    def export_to_file(self, file_path: str) -> None: ...

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
        result: Result[AlgorithmConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
            benchmark_add_algorithm(
                self.name, algorithm.name, algorithm._to_domain_algorithm(), algorithm._to_domain_backend()
            )
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
            raise RuntimeError(error)
        success: AlgorithmConfigDomain = result.unwrap()
        self.algorithms.append(Algorithm._from_domain(success))

    def remove_algorithm(
        self,
        algorithm: str | Algorithm,
        benchmark_remove_algorithm: BenchmarkRemoveMetricUc = Provide[UsecaseContainer.benchmark_remove_algorithm_uc],
    ) -> None:
        algorithm_name = algorithm.name if isinstance(algorithm, Algorithm) else algorithm

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_algorithm(
            self.name, algorithm_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.algorithms, algorithm_name)

    def add_plot(
        self, plot: Plot, benchmark_add_plot: BenchmarkAddPlotUc = Provide[UsecaseContainer.benchmark_add_plot_uc]
    ) -> None:
        result: Result[PlotConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
            benchmark_add_plot(self.name, plot.name, plot._to_domain_config())
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add plot to benchmark: {error}")
            raise RuntimeError(error)
        success: PlotConfigDomain = result.unwrap()
        self.plots.append(Plot._from_domain(success))

    def remove_plot(
        self,
        plot: str | Plot,
        benchmark_remove_plot: BenchmarkRemovePlotUc = Provide[UsecaseContainer.benchmark_remove_plot_uc],
    ) -> None:
        plot_name = plot.name if isinstance(plot, Plot) else plot

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_plot(self.name, plot_name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove plot to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.plots, plot_name)

    def run_model_metrics(self) -> None: ...
    def run_metrics(self) -> None: ...
    def run_plots(self) -> None: ...
    def run_jobs(self) -> None: ...

    def list_model_metrics_classes(self) -> list[None]: ...
    def list_metrics_classes(self) -> list[None]: ...
    def list_plots_classes(self) -> list[None]: ...
    def list_algorithms(self) -> list[None]: ...
    def list_backends(self) -> list[None]: ...

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
