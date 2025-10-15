from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import MetricDomain, RegisteredDataDomain
from luna_bench._internal.interfaces import IMetric
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models import MetricUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class MetricMapper:
    @staticmethod
    def to_user_model(
        metric_domain: MetricDomain, metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain]
    ) -> Result[MetricUserModel, UnknownIdError | ValidationError]:
        """
        Convert the algorithm domain to the user model.

        Parameters
        ----------
        metric_domain: MetricDomain
            The model to convert.
        metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain]
            The registry to use for the conversion.

        Returns
        -------
        Result[MetricUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[IMetric, UnknownIdError | ValidationError] = metric_registry.from_domain_to_user_model(
            metric_domain.config_data
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            MetricUserModel.model_construct(
                name=metric_domain.name, status=metric_domain.status, metric=user_config.unwrap()
            )
        )
