from dependency_injector.wiring import Provide, inject
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import BenchmarkDomain, RegisteredDataDomain
from luna_bench._internal.interfaces import IFeature, IMetric, IPlot
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.user_models import (
    BenchmarkUserModel,
)
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkLoadAllUc
from .utils import convert_to_user_model


class BenchmarkLoadAllUcImpl(BenchmarkLoadAllUc):
    _transaction: DaoTransaction

    _metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain]
    _feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain]
    _algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
    _plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain] = Provide[RegistryContainer.metric_registry],
        feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain] = Provide[
            RegistryContainer.feature_registry
        ],
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_registry
        ],
        plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain] = Provide[RegistryContainer.plot_registry],
    ) -> None:
        """
        Initialize the BenchmarkLoadAllUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

        self._metric_registry = metric_registry
        self._feature_registry = feature_registry
        self._algorithm_registry = algorithm_registry
        self._plot_registry = plot_registry

    def __call__(self) -> Result[list[BenchmarkUserModel], UnknownLunaBenchError | UnknownIdError | ValidationError]:
        with self._transaction as t:
            result_dao: Result[list[BenchmarkDomain], UnknownLunaBenchError] = t.benchmark.load_all()

            to_return: list[BenchmarkUserModel] = []

            if not is_successful(result_dao):
                return Failure(result_dao.failure())
            benchmark_domains: list[BenchmarkDomain] = result_dao.unwrap()

            for benchmark_domain in benchmark_domains:
                user_model = convert_to_user_model(
                    benchmark_domain,
                    self._metric_registry,
                    self._feature_registry,
                    self._algorithm_registry,
                    self._plot_registry,
                )
                if not is_successful(user_model):
                    return Failure(user_model.failure())
                to_return.append(user_model.unwrap())
            return Success(to_return)
