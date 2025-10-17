from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.domain_models.plot_config_domain import PlotDomain
from luna_bench._internal.interfaces import IPlot
from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models.plot_usermodel import PlotUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class PlotMapper(ModelListMixin[PlotDomain, PlotUserModel]):
    def __init__(
        self,
        plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain],
    ) -> None:
        self._plot_registry = plot_registry

    def to_user_model(
        self,
        domain: PlotDomain,
    ) -> Result[PlotUserModel, UnknownIdError | ValidationError]:
        """
        Convert the plot domain to the user model.

        Parameters
        ----------
        plot_domain: FeatureDomain
            The model to convert.

        Returns
        -------
        Result[FeatureUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[IPlot, UnknownIdError | ValidationError] = self._plot_registry.from_domain_to_user_model(
            domain.config_data
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            PlotUserModel.model_construct(
                name=domain.name,
                status=domain.status,
                plot=user_config.unwrap(),
            )
        )
