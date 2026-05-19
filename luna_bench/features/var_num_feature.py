from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import BaseFeature, FeatureResult, feature

if TYPE_CHECKING:
    from luna_model import Model


class VarNumberFeatureResult(FeatureResult):
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
