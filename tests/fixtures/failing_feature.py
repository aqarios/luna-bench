from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model


class FailingFeatureResult(ArbitraryDataDomain):
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
