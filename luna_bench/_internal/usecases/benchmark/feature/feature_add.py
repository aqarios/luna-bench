from dependency_injector.wiring import Provide, inject
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import FeatureDomain, RegisteredDataDomain
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import FeatureAddUc
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class FeatureAddUcImpl(FeatureAddUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[IFeature, RegisteredDataDomain]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry: PydanticRegistry[IFeature, RegisteredDataDomain] = Provide[RegistryContainer.feature_registry],
    ) -> None:
        """
        Initialize the BenchmarkAddFeatureUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry = registry

    def __call__(
        self, benchmark_name: str, name: str, feature: IFeature
    ) -> Result[
        FeatureUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        dm_result: Result[RegisteredDataDomain, UnknownComponentError] = self._registry.from_user_model_to_domain_model(
            feature
        )
        if not is_successful(dm_result):
            return Failure(dm_result.failure())
        dm: RegisteredDataDomain = dm_result.unwrap()

        with self._transaction as t:
            result: Result[FeatureDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
                t.feature.add(benchmark_name, name, dm.registered_id, dm.data)
            )
            if not is_successful(result):
                return Failure(result.failure())

            config: Result[IFeature, UnknownIdError | ValidationError] = self._registry.from_domain_to_user_model(
                result.unwrap().config_data
            )

            if not is_successful(config):
                return Failure(config.failure())

            return Success(
                FeatureUserModel(
                    name=name,
                    status=result.unwrap().status,
                    feature=config.unwrap(),
                )
            )
