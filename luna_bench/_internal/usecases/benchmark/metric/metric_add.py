from dependency_injector.wiring import Provide, inject
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import MetricDomain, RegisteredDataDomain
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import MetricAddUc
from luna_bench.custom import BaseMetric
from luna_bench.entities import MetricEntity
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class MetricAddUcImpl(MetricAddUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[BaseMetric, RegisteredDataDomain]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry: PydanticRegistry[BaseMetric, RegisteredDataDomain] = Provide[RegistryContainer.metric_registry],
    ) -> None:
        """
        Initialize the BenchmarkMetricImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry = registry

    def __call__(
        self, benchmark_name: str, name: str, metric: BaseMetric
    ) -> Result[
        MetricEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        dm_result: Result[RegisteredDataDomain, UnknownComponentError] = self._registry.from_user_model_to_domain_model(
            metric
        )
        if not is_successful(dm_result):
            return Failure(dm_result.failure())
        dm: RegisteredDataDomain = dm_result.unwrap()

        with self._transaction as t:
            result: Result[MetricDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = t.metric.add(
                benchmark_name, name, dm.registered_id, dm.data
            )
            if not is_successful(result):
                return Failure(result.failure())

            config: Result[BaseMetric, UnknownIdError | ValidationError] = self._registry.from_domain_to_user_model(
                result.unwrap().config_data
            )

            if not is_successful(config):
                return Failure(config.failure())

            return Success(
                MetricEntity(
                    name=name,
                    status=result.unwrap().status,
                    metric=config.unwrap(),
                    results={},
                )
            )
