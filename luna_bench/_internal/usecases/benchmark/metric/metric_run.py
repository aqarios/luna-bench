import time
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import JobStatus, MetricResultDomain, RegisteredDataDomain
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import MetricRunUc
from luna_bench._internal.user_models import BenchmarkUserModel, MetricUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench._internal.user_models.metric_result_usermodel import MetricResultUserModel
from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.algorithm_not_done import AlgorithmNotDoneError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.types import FeatureConfig, FeatureName, FeatureResult, ModelName

if TYPE_CHECKING:
    from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain


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

    def _run(
        self,
        benchmark_name: str,
        alogorithm_name: str,
        model_name: str,
        algorithm_result: AlgorithmResultUserModel,
        feature_results: FeatureResults,
        metric: MetricUserModel,
    ) -> Result[MetricResultUserModel, AlgorithmNotDoneError | DataNotExistError | UnknownLunaBenchError]:
        # CHECK if result for metric and algorithm already exists and if it should be updated/recalulated or not.

        result: MetricResultUserModel | None = metric.results.get((alogorithm_name, model_name), None)

        if result is not None and result.status == JobStatus.DONE:
            self._logger.info(
                f"Metric {metric.name} for model {model_name} and algorithm {alogorithm_name} "
                f"already exists and is done."
            )
            return Success(result)

        if algorithm_result.status != JobStatus.DONE:
            return Failure(AlgorithmNotDoneError(alogorithm_name, algorithm_result.status))

        if algorithm_result.solution is None:
            return Failure(DataNotExistError())

        user_result: ArbitraryDataDomain | None = None
        exception: str | None = None
        status: JobStatus

        start = time.perf_counter_ns()

        try:
            user_result = metric.metric.run(algorithm_result.solution, feature_results)
            status = JobStatus.DONE
        except Exception as e:
            status = JobStatus.FAILED
            exception = str(e)

        end = time.perf_counter_ns()

        delta_time = (end - start) // 1_000_000

        # Save result. Doesn't matter if it failed or not, we have to save it anyway.
        result_domain = MetricResultDomain.model_construct(
            processing_time_ms=delta_time,
            model_name=model_name,
            algorithm_name=alogorithm_name,
            result=user_result,
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
        metric.results[(alogorithm_name, model_name)] = result
        return Success(result)

    def _create_feature_result_lookup(
        self, benchmark: BenchmarkUserModel
    ) -> dict[tuple[type[BaseFeature], ModelName], dict[FeatureName, tuple[FeatureResult, FeatureConfig]]]:
        feature_map: dict[
            tuple[type[BaseFeature], ModelName], dict[FeatureName, tuple[FeatureResult, FeatureConfig]]
        ] = {}
        for f in benchmark.features:
            feature_type: type[BaseFeature] = type(f.feature)
            feature_config: FeatureConfig = f.feature
            for f_model_name, result in f.results.items():
                r: FeatureResult = result.result
                if r is not None:
                    feature_map.setdefault((feature_type, f_model_name), {})[f.name] = (r, feature_config)

        return feature_map

    def _create_and_check_feature_results(
        self,
        benchmark: BenchmarkUserModel,
        model_name: ModelName,
        metric: MetricUserModel,
        feature_lookup_table: dict[
            tuple[type[BaseFeature], ModelName], dict[FeatureName, tuple[FeatureResult, FeatureConfig]]
        ],
    ) -> Result[FeatureResults, RunFeatureMissingError]:
        feature_data: dict[type[BaseFeature], dict[FeatureName, tuple[FeatureResult, FeatureConfig]]] = {}

        required_features = metric.metric.required_features  # Set in the decorator
        if required_features is not None:
            for f in required_features:
                key = (f, model_name)
                if key not in feature_lookup_table:
                    return Failure(RunFeatureMissingError(f, benchmark.name))
                feature_data[f] = feature_lookup_table[key].copy()

        return Success(
            FeatureResults(
                data=feature_data,
                allowed=required_features,
            )
        )

    def __call__(
        self, benchmark: BenchmarkUserModel, metric: MetricUserModel | None = None
    ) -> Result[None, RunMetricMissingError | RunModelsetMissingError]:
        metrics: list[MetricUserModel]
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
                        return feature_results.failure()

                    metric_result = self._run(benchmark.name, a.name, model_name, result, feature_results.unwrap(), m)

                    if not is_successful(metric_result):
                        pass  # TODO(Llewellyn): decide what to do with the failed run # noqa: FIX002

        return Success(None)
