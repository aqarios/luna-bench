from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import PlotDomain, RegisteredDataDomain
from luna_bench._internal.interfaces import IPlot
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models import PlotUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class PlotMapper:
    @staticmethod
    def to_user_model(
        plot_domain: PlotDomain, plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain]
    ) -> Result[PlotUserModel, UnknownIdError | ValidationError]:
        """
        Convert the plot domain to the user model.

        Parameters
        ----------
        plot_domain: FeatureDomain
            The model to convert.
        plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain]
            The registry to use for the conversion.

        Returns
        -------
        Result[FeatureUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[IPlot, UnknownIdError | ValidationError] = plot_registry.from_domain_to_user_model(
            plot_domain.config_data
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            PlotUserModel.model_construct(name=plot_domain.name, status=plot_domain.status, plot=user_config.unwrap())
        )
