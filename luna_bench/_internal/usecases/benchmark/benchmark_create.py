from dependency_injector.wiring import Provide, inject
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.result import Result

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import BenchmarkDomain, RegisteredDataDomain
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkCreateUc
from .utils import convert_return_to_user_model


class BenchmarkCreateUcImpl(BenchmarkCreateUc):
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
        Initialize the BenchmarkCreateImpl with a dao transaction.

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

    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError]:
        with self._transaction as t:
            result_dao: Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError] = t.benchmark.create(
                benchmark_name
            )
            return convert_return_to_user_model(
                result_dao,
                self._metric_registry,
                self._feature_registry,
                self._algorithm_registry,
                self._plot_registry,
            )
