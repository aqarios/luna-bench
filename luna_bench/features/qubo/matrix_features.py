from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import BaseFeature, feature
from luna_bench.custom.base_results.feature_result import FeatureResult

from .get_qubo import get_qubo

if TYPE_CHECKING:
    from luna_model import Model


from luna_bench.helpers.numpy_stats_helper import NumpyStatsHelper


class QuboMatrixFeatureResult(FeatureResult):
    """Result container for matrix statistical QUBO features.

    Attributes
    ----------
    mean
        Mean of all matrix entries.
    median
        Median of all matrix entries.
    variance
        Variance of all matrix entries.
    minium
        Minimum matrix entry.
    maximum
        Maximum matrix entry.
    std
        Standard deviation of all matrix entries.
    skewness
        Asymmetry of the value distribution. Positive means a longer right
        tail (many small values, few large); negative means the opposite.
        Zero indicates a symmetric distribution.
    kurtosis
        Tailedness of the value distribution (excess kurtosis, so a normal
        distribution has kurtosis 0). Positive values indicate heavier tails
        and more outliers; negative values indicate lighter tails.
    q10
        10th percentile of all matrix entries.
    q90
        90th percentile of all matrix entries.
    vc
        Coefficient of variation (std / mean). Measures relative dispersion;
        higher values indicate more spread relative to the mean.
    """

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
class QuboMatrixFeature(BaseFeature[QuboMatrixFeatureResult]):
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
