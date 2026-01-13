from __future__ import annotations

import random
from typing import TYPE_CHECKING

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model


class FakeFeatureResult(ArbitraryDataDomain):
    """Fake feature result class."""

    random_number: int
    fake_feature_model_name: str


@feature
class FakeFeature(IFeature):
    """Fake feature class."""

    def run(self, model: Model) -> FakeFeatureResult:
        """
        Fake feature which will return a random number.

        Parameters
        ----------
        model: Model
            The model for which the feature should be calculated

        """
        return FakeFeatureResult(
            random_number=random.randint(0, 100),  # noqa: S311
            fake_feature_model_name=model.name,
        )
