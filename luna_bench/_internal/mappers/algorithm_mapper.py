from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import AlgorithmDomain, AlgorithmResultDomain, RegisteredDataDomain
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models import AlgorithmUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class AlgorithmMapper(ModelListMixin[AlgorithmDomain, AlgorithmUserModel]):
    def __init__(
        self,
        algorithm_sync_registry: PydanticRegistry[AlgorithmSync, RegisteredDataDomain],
        algorithm_async_registry: PydanticRegistry[AlgorithmAsync[BaseModel], RegisteredDataDomain],
    ) -> None:
        self._algorithm_sync_registry = algorithm_sync_registry
        self._algorithm_async_registry = algorithm_async_registry

    @staticmethod
    def result_to_domain_model(result: AlgorithmResultUserModel) -> AlgorithmResultDomain:
        to_return = AlgorithmResultDomain.model_construct(
            meta_data=result.meta_data,
            status=result.status,
            error=result.error,
            task_id=result.task_id,
            retrival_data=result.retrival_data,
            model_id=result.model_id,
        )
        to_return.solution = result.solution

        return to_return

    @staticmethod
    def result_to_user_model(result: AlgorithmResultDomain) -> AlgorithmResultUserModel:
        return AlgorithmResultUserModel.model_construct(
            meta_data=result.meta_data,
            status=result.status,
            error=result.error,
            solution=result.solution,
            task_id=result.task_id,
            retrival_data=result.retrival_data,
            model_id=result.model_id,
        )

    @staticmethod
    def result_to_user_model_dict(results: dict[str, AlgorithmResultDomain]) -> dict[str, AlgorithmResultUserModel]:
        return {k: AlgorithmMapper.result_to_user_model(result) for k, result in results.items()}

    def to_user_model(
        self,
        domain: AlgorithmDomain,
    ) -> Result[AlgorithmUserModel, UnknownIdError | ValidationError]:
        """
        Convert the algorithm domain to the user model.

        Parameters
        ----------
        algorithm_domain: AlgorithmDomain
            The model to convert.

        Returns
        -------
        Result[AlgorithmUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[AlgorithmSync | AlgorithmAsync[BaseModel], UnknownIdError | ValidationError]
        match domain.algorithm_type:
            case AlgorithmType.SYNC:
                user_config = self._algorithm_sync_registry.from_domain_to_user_model(domain.config_data)

            case AlgorithmType.ASYNC:
                user_config = self._algorithm_async_registry.from_domain_to_user_model(domain.config_data)

        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            AlgorithmUserModel.model_construct(
                name=domain.name,
                status=domain.status,
                algorithm=user_config.unwrap(),
                results=self.result_to_user_model_dict(domain.results),
            )
        )
