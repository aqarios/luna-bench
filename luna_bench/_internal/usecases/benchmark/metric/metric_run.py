import time
from itertools import product
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import MetricResultDomain, RegisteredDataDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.helper import FeatureResultBuilder
from luna_bench._internal.usecases.benchmark.protocols import MetricRunUc
from luna_bench.custom import BaseMetadataMetric, BaseMetric
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.custom.result_containers.solve_metadata import SolveMetadata
from luna_bench.entities import AlgorithmResultEntity, BenchmarkEntity, MetricEntity, MetricResultEntity
from luna_bench.entities.enums import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.algorithm_not_done import AlgorithmNotDoneError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from luna_bench.custom.base_results.metric_result import MetricResult


class MetricRunUcImpl(MetricRunUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[BaseMetric, RegisteredDataDomain]
    _logger = BenchLogger.get_logger(__name__)

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry: PydanticRegistry[BaseMetric, RegisteredDataDomain] = Provide[RegistryContainer.metric_registry],
    ) -> None:
        """
        Initialize the MetricRunUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry = registry

    def _run(  # noqa: PLR0913, PLR0917
        self,
        benchmark_name: str,
        algorithm_name: str,
        model_name: str,
        algorithm_result: AlgorithmResultEntity,
        feature_results: FeatureResultContainer,
        metric: MetricEntity,
    ) -> Result[MetricResultEntity, AlgorithmNotDoneError | DataNotExistError | UnknownLunaBenchError]:
        # CHECK if result for metric and algorithm already exists and if it should be updated/recalulated or not.

        repetition = algorithm_result.repetition
        existing: list[MetricResultEntity] = metric.results.get(model_name, {}).get(algorithm_name, [])
        result: MetricResultEntity | None = next((r for r in existing if r.repetition == repetition), None)

        if result is not None and result.status == JobStatus.DONE:
            self._logger.info(
                f"Metric {metric.name} for model {model_name}, algorithm {algorithm_name} and "
                f"repetition {repetition} already exists and is done."
            )
            return Success(result)

        if algorithm_result.status != JobStatus.DONE:
            return Failure(AlgorithmNotDoneError(algorithm_name, algorithm_result.status))

        if algorithm_result.solution is None:
            return Failure(DataNotExistError())

        user_result: MetricResult | None = None
        exception: str | None = None
        status: JobStatus

        start = time.perf_counter_ns()

        try:
            if isinstance(metric.metric, BaseMetadataMetric):
                # Only a metadata metric is told which run it is looking at. One that reads
                # metadata a run never reported raises, and lands in the except below as a
                # failed result for this pair alone.
                user_result = metric.metric.run_with_metadata(
                    algorithm_result.solution,
                    feature_results,
                    SolveMetadata.of(algorithm_result.metadata),
                )
            else:
                user_result = metric.metric.run(algorithm_result.solution, feature_results)
            status = JobStatus.DONE
        except Exception as e:
            self._logger.error(
                f"Metric '{metric.name}' failed on model '{model_name}' for algorithm '{algorithm_name}' "
                f"(repetition {repetition}):",
                exc_info=True,
            )
            status = JobStatus.FAILED
            exception = str(e)

        end = time.perf_counter_ns()

        delta_time = (end - start) // 1_000_000

        # Save result. Doesn't matter if it failed or not, we have to save it anyway.
        result_domain = MetricResultDomain.model_construct(
            processing_time_ms=delta_time,
            model_name=model_name,
            algorithm_name=algorithm_name,
            repetition=repetition,
            result=ArbitraryDataDomain.model_construct(**user_result.model_dump()) if user_result else None,
            status=status,
            error=exception,
        )
        with self._transaction as t:
            r: Result[None, DataNotExistError | UnknownLunaBenchError] = t.metric.set_result(
                benchmark_name,
                metric.name,
                result_domain,
            )
        if not is_successful(r):
            return Failure(r.failure())

        result = MetricMapper.result_to_user_model(result_domain)
        per_repetition = metric.results.setdefault(model_name, {}).setdefault(algorithm_name, [])
        # A repetition that failed before is replaced rather than appended, so re-running
        # a benchmark leaves one result per run instead of a growing pile of attempts.
        replaced = next((i for i, r in enumerate(per_repetition) if r.repetition == repetition), None)
        if replaced is None:
            per_repetition.append(result)
            # A repetition whose result was computed late - it failed to store the first
            # time, while later ones went through - belongs where a reload would put it.
            per_repetition.sort(key=lambda r: r.repetition)
        else:
            per_repetition[replaced] = result
        return Success(result)

    def __call__(
        self, benchmark: BenchmarkEntity, metric: MetricEntity | None = None
    ) -> Result[None, RunMetricMissingError | RunModelsetMissingError | RunFeatureMissingError]:
        metrics: list[MetricEntity]
        if metric is not None:
            # Check if the feature is part of the benchmark
            if metric not in benchmark.metrics:
                return Failure(RunMetricMissingError(metric.name, benchmark.name))
            metrics = [metric]
        else:
            metrics = benchmark.metrics

        feature_builder = FeatureResultBuilder(benchmark)

        for a in benchmark.algorithms:
            for model_name, runs in a.results.items():
                for result, m in product(runs, metrics):
                    feature_results = feature_builder.results(model_name, m.metric.required_features)

                    if not is_successful(feature_results):
                        return Failure(feature_results.failure())

                    metric_result = self._run(benchmark.name, a.name, model_name, result, feature_results.unwrap(), m)

                    if not is_successful(metric_result):
                        self._logger.warning(
                            f"Algorithm '{a.name}' failed on model '{model_name}' "
                            f"and will be skipped for metric '{m.name}'."
                        )

        return Success(None)
