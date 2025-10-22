from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import AlgorithmDomain, RegisteredDataDomain
from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models import AlgorithmUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class AlgorithmMapper(ModelListMixin[AlgorithmDomain, AlgorithmUserModel]):
    def __init__(
        self,
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain],
    ) -> None:
        self._algorithm_registry = algorithm_registry

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
        user_config: Result[IAlgorithm[IBackend], UnknownIdError | ValidationError] = (
            self._algorithm_registry.from_domain_to_user_model(domain.config_data)
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            AlgorithmUserModel.model_construct(
                name=domain.name,
                status=domain.status,
                algorithm=user_config.unwrap(),
            )
        )
