from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.helpers import feature

from .get_qubo import get_qubo

if TYPE_CHECKING:
    from luna_quantum import Model


from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper


class QuboMatrixFeatureResult(ArbitraryDataDomain):
    """Result container for matrix statistical QUBO features."""

    mean: float
    median: float
    variance: float
    minium: float
    maximum: float
    std: float
    skewness: float
    kurtosis: float
    q10: float
    q90: float
    vc: float


@feature
class QuboMatrixFeature(BaseFeature):
    """Extract statistical matrix features from QUBO models.

    Compute descriptive statistics over all entries of the QUBO matrix.

    Extracted features include:

    - **Central tendency / dispersion**: Mean, median, variance, standard
      deviation, minimum, and maximum.
    - **Shape**: Skewness and kurtosis of the flattened matrix.
    - **Quantiles**: 10th and 90th percentiles (q10, q90) and the
      variation coefficient (vc).
    """

    def run(self, model: Model) -> QuboMatrixFeatureResult:
        """Compute matrix statistical features for the given model.

        Parameters
        ----------
        model : Model
            The optimization model to extract features from.

        Returns
        -------
        QuboMatrixFeatureResult
            A result object containing the computed matrix statistics.
        """
        qubo = get_qubo(model)

        return QuboMatrixFeatureResult(
            mean=NumpyStatsHelper.mean(qubo),
            median=NumpyStatsHelper.median(qubo),
            variance=NumpyStatsHelper.var(qubo),
            minium=NumpyStatsHelper.min(qubo),
            maximum=NumpyStatsHelper.max(qubo),
            std=NumpyStatsHelper.std(qubo),
            skewness=NumpyStatsHelper.skew(qubo.flatten()),
            kurtosis=NumpyStatsHelper.kurtosis(qubo.flatten()),
            q10=NumpyStatsHelper.q10(qubo),
            q90=NumpyStatsHelper.q90(qubo),
            vc=NumpyStatsHelper.vc(qubo),
        )
