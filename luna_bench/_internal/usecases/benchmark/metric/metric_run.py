import time

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import MetricResultDomain, RegisteredDataDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import MetricRunUc
from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.entities import AlgorithmResultEntity, BenchmarkEntity, MetricEntity, MetricResultEntity
from luna_bench.entities.enums import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.algorithm_not_done import AlgorithmNotDoneError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.types import FeatureName, FeatureResult, MetricResult, ModelName


class MetricRunUcImpl(MetricRunUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[BaseMetric, RegisteredDataDomain]
    _logger = Logging.get_logger(__name__)

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

    def _run(  # noqa: PLR0913
        self,
        benchmark_name: str,
        algorithm_name: str,
        model_name: str,
        algorithm_result: AlgorithmResultEntity,
        feature_results: FeatureResults,
        metric: MetricEntity,
    ) -> Result[MetricResultEntity, AlgorithmNotDoneError | DataNotExistError | UnknownLunaBenchError]:
        # CHECK if result for metric and algorithm already exists and if it should be updated/recalulated or not.

        result: MetricResultEntity | None = metric.results.get((algorithm_name, model_name), None)

        if result is not None and result.status == JobStatus.DONE:
            self._logger.info(
                f"Metric {metric.name} for model {model_name} and algorithm {algorithm_name} "
                f"already exists and is done."
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
            user_result = metric.metric.run(algorithm_result.solution, feature_results)
            status = JobStatus.DONE
        except Exception as e:
            self._logger.error(
                f"Metric '{metric.name}' failed on model '{model_name}' for algorithm '{algorithm_name}':",
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
        metric.results[(algorithm_name, model_name)] = result
        return Success(result)

    @staticmethod
    def _create_feature_result_lookup(
        benchmark: BenchmarkEntity,
    ) -> dict[tuple[type[BaseFeature], ModelName], dict[FeatureName, tuple[FeatureResult, BaseFeature]]]:
        feature_map: dict[
            tuple[type[BaseFeature], ModelName], dict[FeatureName, tuple[FeatureResult, BaseFeature]]
        ] = {}
        for f in benchmark.features:
            feature_type: type[BaseFeature] = type(f.feature)
            feature_config: BaseFeature = f.feature
            for f_model_name, result in f.results.items():
                r: FeatureResult | None = result.result
                if r is not None:
                    feature_map.setdefault((feature_type, f_model_name), {})[f.name] = (r, feature_config)

        return feature_map

    def _create_and_check_feature_results(
        self,
        benchmark: BenchmarkEntity,
        model_name: ModelName,
        metric: MetricEntity,
        feature_lookup_table: dict[
            tuple[type[BaseFeature], ModelName], dict[FeatureName, tuple[FeatureResult, BaseFeature]]
        ],
    ) -> Result[FeatureResults, RunFeatureMissingError]:
        feature_data: dict[type[BaseFeature], dict[FeatureName, tuple[FeatureResult, BaseFeature]]] = {}

        required_features = metric.metric.required_features  # Set in the decorator
        for f in required_features:
            key = (f, model_name)
            if key not in feature_lookup_table:
                return Failure(RunFeatureMissingError(f.__name__, benchmark.name))
            feature_data[f] = feature_lookup_table[key].copy()

        return Success(
            FeatureResults(
                data=feature_data,
                allowed=required_features,
            )
        )

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

        feature_map = self._create_feature_result_lookup(benchmark)

        for a in benchmark.algorithms:
            for model_name, result in a.results.items():
                for m in metrics:
                    feature_results = self._create_and_check_feature_results(benchmark, model_name, m, feature_map)

                    if not is_successful(feature_results):
                        return Failure(feature_results.failure())

                    metric_result = self._run(benchmark.name, a.name, model_name, result, feature_results.unwrap(), m)

                    if not is_successful(metric_result):
                        pass  # TODO(Llewellyn): decide what to do with the failed run # noqa: FIX002

        return Success(None)
