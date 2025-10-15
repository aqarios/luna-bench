from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import AlgorithmDomain, RegisteredDataDomain
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models import AlgorithmUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class AlgorithmMapper:
    @staticmethod
    def to_user_model(
        algorithm_domain: AlgorithmDomain,
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain],
    ) -> Result[AlgorithmUserModel, UnknownIdError | ValidationError]:
        """
        Convert the algorithm domain to the user model.

        Parameters
        ----------
        algorithm_domain: AlgorithmDomain
            The model to convert.
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]
            The registry to use for the conversion.

        Returns
        -------
        Result[AlgorithmUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[IAlgorithm[IBackend], UnknownIdError | ValidationError] = (
            algorithm_registry.from_domain_to_user_model(algorithm_domain.config_data)
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            AlgorithmUserModel.model_construct(
                name=algorithm_domain.name, status=algorithm_domain.status, algorithm=user_config.unwrap()
            )
        )
