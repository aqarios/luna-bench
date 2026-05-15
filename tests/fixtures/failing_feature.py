from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import BaseFeature, feature
from luna_bench.custom.base_results.feature_result import FeatureResult

if TYPE_CHECKING:
    from luna_model import Model


class FailingFeatureResult(FeatureResult):
    """Fake feature result class."""

    random_number: int


@feature
class FailingFeature(BaseFeature):
    """Failing feature class."""

    def run(self, model: Model) -> FailingFeatureResult:  # noqa: ARG002
        """
        Failing feature which will return a random number.

        Parameters
        ----------
        model: Model
            The model for which the feature should be calculated

        """
        msg = "Failing Feature because of Value Error"
        raise ValueError(msg)
