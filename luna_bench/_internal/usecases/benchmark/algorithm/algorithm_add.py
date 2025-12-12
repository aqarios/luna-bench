from typing import TYPE_CHECKING, Any

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmAddUc
from luna_bench._internal.user_models.algorithm_usermodel import AlgorithmUserModel
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench._internal.domain_models.algorithm_domain import AlgorithmDomain


class AlgorithmAddUcImpl(AlgorithmAddUc):
    _transaction: DaoTransaction
    _registry_sync: PydanticRegistry[BaseAlgorithmSync, RegisteredDataDomain]
    _registry_async: PydanticRegistry[BaseAlgorithmAsync[BaseModel], RegisteredDataDomain]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry_sync: PydanticRegistry[BaseAlgorithmSync, RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_sync_registry
        ],
        registry_async: PydanticRegistry[BaseAlgorithmAsync[BaseModel], RegisteredDataDomain] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
    ) -> None:
        """
        Initialize the BenchmarkAddAlgorithmUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry_sync = registry_sync
        self._registry_async = registry_async

    def __call__(
        self, benchmark_name: str, name: str, algorithm: BaseAlgorithmSync | BaseAlgorithmAsync[Any]
    ) -> Result[
        AlgorithmUserModel,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        dm_result: Result[RegisteredDataDomain, UnknownComponentError]

        if isinstance(algorithm, BaseAlgorithmAsync):
            dm_result = self._registry_async.from_user_model_to_domain_model(algorithm)
        elif isinstance(algorithm, BaseAlgorithmSync):
            dm_result = self._registry_sync.from_user_model_to_domain_model(algorithm)

        if not is_successful(dm_result):
            return Failure(dm_result.failure())
        dm: RegisteredDataDomain = dm_result.unwrap()

        with self._transaction as t:
            result: Result[AlgorithmDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError] = (
                t.algorithm.add(
                    benchmark_name,
                    name,
                    dm.registered_id,
                    AlgorithmType.SYNC if isinstance(algorithm, BaseAlgorithmSync) else AlgorithmType.ASYNC,
                    dm.data,
                )
            )
            if not is_successful(result):
                return Failure(result.failure())
            domain_model = result.unwrap()

            config: (
                Result[BaseAlgorithmSync | BaseAlgorithmAsync[BaseModel], UnknownIdError | ValidationError]
                | Result[BaseAlgorithmSync, UnknownIdError | ValidationError]
            )
            match domain_model.algorithm_type:
                case AlgorithmType.SYNC:
                    config = self._registry_sync.from_domain_to_user_model(result.unwrap().config_data)
                case AlgorithmType.ASYNC:
                    config = self._registry_async.from_domain_to_user_model(result.unwrap().config_data)

            if not is_successful(config):
                return Failure(config.failure())
            return Success(
                AlgorithmUserModel.model_construct(
                    name=name, status=result.unwrap().status, algorithm=config.unwrap(), results={}
                )
            )
