from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Result

from luna_bench import UsecaseContainer
from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
from luna_bench._internal.usecases.benchmark.protocols import BenchmarkCreateUc
from luna_bench.components.job import Job
from luna_bench.components.metric import Metric
from luna_bench.components.model_metric import ModelMetric
from luna_bench.components.model_set import ModelSet
from luna_bench.components.plot import Plot
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
    from luna_quantum.solve.interfaces.backend_i import IBackend




class Benchmark(BaseModel):
    _logger = Logging.get_logger(__name__)

    name: str
    modelset: ModelSet
    model_metrics: list[ModelMetric]
    metrics: list[Metric]
    jobs: list[Job]
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
    def load(name: str) -> Benchmark: ...

    @staticmethod
    def load_all() -> list[Benchmark]: ...

    def run(self) -> None: ...

    def reset(self) -> None: ...

    def export_to_file(self, file_path: str) -> None: ...

    @property
    def modelset(self) -> ModelSet: ...

    @modelset.setter
    def modelset(self, value: ModelSet) -> None: ...

    def add_model_metric(self, model_metric: ModelMetric) -> None: ...
    def remove_model_metric(self, model_metric: ModelMetric) -> None: ...
    def list_model_metrics(self) -> list[ModelMetric]: ...
    def reset_model_metrics(self) -> None: ...

    def add_metric(self, metric: Metric) -> None: ...
    def remove_metric(self, metric: Metric) -> None: ...
    def list_metrics(self) -> list[Metric]: ...
    def reset_metrics(self) -> None: ...

    def add_job(self, algorithm: IAlgorithm, backend: IBackend | None = None) -> None: ...
    def remove_job(self, algorithm: IAlgorithm, backend: IBackend | None = None) -> None: ...
    def list_jobs(self) -> list[Job]: ...
    def reset_jobs(self) -> None: ...

    def add_plot(self, plot: Plot) -> None: ...
    def remove_plot(self, plot: Plot) -> None: ...
    def list_plots(self) -> list[Plot]: ...
    def reset_plots(self) -> None: ...

    def run_model_metrics(self) -> None: ...
    def run_metrics(self) -> None: ...
    def run_plots(self) -> None: ...
    def run_jobs(self) -> None: ...

    @staticmethod
    def _to_benchmark(benchmark: BenchmarkDomain) -> Benchmark:
        return Benchmark(
            name=benchmark.name,
            modelset=ModelSet._to_data_set(benchmark.modelset),
            model_metrics=[],
            metrics=[],
            jobs=[],
            plots=[],
        )
