from typing import Any

from dependency_injector.wiring import Provide, inject
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import PlotDomain, RegisteredDataDomain
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import PlotAddUc
from luna_bench._internal.user_models import PlotUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class PlotAddUcImpl(PlotAddUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[IPlot[Any], RegisteredDataDomain]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry: PydanticRegistry[IPlot[Any], RegisteredDataDomain] = Provide[RegistryContainer.plot_registry],
    ) -> None:
        """
        Initialize the BenchmarkAddPlotUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry = registry

    def __call__(
        self, benchmark_name: str, name: str, plot: IPlot[Any]
    ) -> Result[
        PlotUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        dm_result: Result[RegisteredDataDomain, UnknownComponentError] = self._registry.from_user_model_to_domain_model(
            plot
        )
        if not is_successful(dm_result):
            return Failure(dm_result.failure())
        dm: RegisteredDataDomain = dm_result.unwrap()

        with self._transaction as t:
            result: Result[PlotDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = t.plot.add(
                benchmark_name, name, dm.registered_id, dm.data
            )
            if not is_successful(result):
                return Failure(result.failure())

            config: Result[IPlot[Any], UnknownIdError | ValidationError] = self._registry.from_domain_to_user_model(
                result.unwrap().config_data
            )

            if not is_successful(config):
                return Failure(config.failure())

            return Success(
                PlotUserModel.model_construct(
                    name=name,
                    status=result.unwrap().status,
                    plot=config.unwrap(),
                )
            )
