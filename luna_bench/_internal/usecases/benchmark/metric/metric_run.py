import time
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import JobStatus, MetricResultDomain, RegisteredDataDomain
from luna_bench._internal.interfaces import IMetric
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import MetricRunUc
from luna_bench._internal.user_models import BenchmarkUserModel, MetricUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench._internal.user_models.metric_result_usermodel import MetricResultUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.algorithm_not_done import AlgorithmNotDoneError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain


class MetricRunUcImpl(MetricRunUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[IMetric, RegisteredDataDomain]
    _logger = Logging.get_logger(__name__)

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry: PydanticRegistry[IMetric, RegisteredDataDomain] = Provide[RegistryContainer.metric_registry],
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
        algorithm_registered_id: str,
        model_name: str,
        algorithm_result: AlgorithmResultUserModel,
        metric: MetricUserModel,
    ) -> Result[MetricResultUserModel, AlgorithmNotDoneError | DataNotExistError | UnknownLunaBenchError]:
        # CHECK if result for metric and algorithm already exists and if it should be updated/recalulated or not.

        result: MetricResultUserModel | None = metric.results.get((algorithm_registered_id, model_name), None)

        if result is not None and result.status == JobStatus.DONE:
            self._logger.info(
                f"Metric {metric.name} for model {model_name} and algorithm {algorithm_registered_id} "
                f"already exists and is done."
            )
            return Success(result)

        if algorithm_result.status != JobStatus.DONE:
            return Failure(AlgorithmNotDoneError(algorithm_registered_id, algorithm_result.status))

        if algorithm_result.solution is None:
            return Failure(DataNotExistError())

        user_result: ArbitraryDataDomain | None = None
        exception: str | None = None
        status: JobStatus

        start = time.perf_counter_ns()

        try:
            user_result = metric.metric.run(algorithm_result.solution)
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
            algorithm_registered_id=algorithm_registered_id,
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
        metric.results[(algorithm_registered_id, model_name)] = result
        return Success(result)

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

        for a in benchmark.algorithms:
            for model_name, result in a.results.items():
                for m in metrics:
                    metric_result = self._run(benchmark.name, a.algorithm._registered_id, model_name, result, m)

                    if not is_successful(metric_result):
                        pass  # TODO(Llewellyn): decide what to do with the failed run # noqa: FIX002

        return Success(None)
