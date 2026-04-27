from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_model import Model


class VarNumberFeatureResult(ArbitraryDataDomain):
    """Fake feature result class."""

    var_number: int


@feature
class VarNumberFeature(BaseFeature[VarNumberFeatureResult]):
    """Fake feature class."""

    def run(self, model: Model) -> VarNumberFeatureResult:
        """
        Fake feature which will return a random number.

        Parameters
        ----------
        model: Model
            The model for which the feature should be calculated

        """
        return VarNumberFeatureResult(var_number=model.num_variables)
