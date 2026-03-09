from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

from .get_qubo import get_qubo

if TYPE_CHECKING:
    from luna_model import Model


class QuboSpectralAnalysisFeatureResult(ArbitraryDataDomain):
    """Result container for spectral analysis QUBO features.

    Eigenvalues and eigenvectors are obtained via ``numpy.linalg.eigh``
    (symmetric matrix decomposition).

    Attributes
    ----------
    mean_eigenvalue
        Mean of all eigenvalues (equals the matrix trace divided by n).
    median_eigenvalue
        Median eigenvalue.
    std_eigenvalue
        Standard deviation of the eigenvalues.
    vc_eigenvalue
        Coefficient of variation (std / mean) of the eigenvalues.
    q90_eigenvalue
        90th percentile of the eigenvalues.
    q10_eigenvalue
        10th percentile of the eigenvalues.
    minimum_eigenvalue
        Smallest eigenvalue.
    maximum_eigenvalue
        Largest eigenvalue.
    dominant_eigenvalue
        Largest eigenvalue by absolute value. Indicates the strongest
        mode of the QUBO interaction structure.
    mean_eigenvector
        Mean over all eigenvector components.
    median_eigenvector
        Median over all eigenvector components.
    std_eigenvector
        Standard deviation over all eigenvector components.
    vc_eigenvector
        Coefficient of variation (std / mean) of all eigenvector components.
    q90_eigenvector
        90th percentile over all eigenvector components.
    q10_eigenvector
        10th percentile over all eigenvector components.
    minimum_eigenvector
        Smallest eigenvector component.
    maximum_eigenvector
        Largest eigenvector component.
    dominant_eigenvector
        Largest eigenvector component by absolute value.
    condition_number
        Ratio of largest to smallest singular value. High values indicate
        the QUBO is ill-conditioned and numerically sensitive.
    """

    # Eigenvalue
    mean_eigenvalue: float
    median_eigenvalue: float
    std_eigenvalue: float
    vc_eigenvalue: float
    q90_eigenvalue: float
    q10_eigenvalue: float
    minimum_eigenvalue: float
    maximum_eigenvalue: float
    dominant_eigenvalue: float
    # Eigenvector
    mean_eigenvector: float
    median_eigenvector: float
    std_eigenvector: float
    vc_eigenvector: float
    q90_eigenvector: float
    q10_eigenvector: float
    minimum_eigenvector: float
    maximum_eigenvector: float
    dominant_eigenvector: float
    # More
    condition_number: float


@feature
class QuboSpectralAnalysisFeature(BaseFeature):
    """Extract spectral analysis features from QUBO models.

    Decompose the QUBO matrix with ``numpy.linalg.eigh`` and compute
    descriptive statistics over eigenvalues and eigenvectors.

    Extracted features include:

    - **Eigenvalue statistics**: Mean, median, std, variation coefficient,
      q10, q90, minimum, maximum, and dominant (largest absolute) eigenvalue.
    - **Eigenvector statistics**: Same set of statistics computed over all
      eigenvector components.
    - **Condition number**: Ratio of largest to smallest singular value,
      indicating numerical stability.
    """

    def run(self, model: Model) -> QuboSpectralAnalysisFeatureResult:
        """Compute spectral analysis features for the given model.

        Parameters
        ----------
        model : Model
            The optimization model to extract features from.

        Returns
        -------
        QuboSpectralAnalysisFeatureResult
            A result object containing the computed spectral features.
        """
        qubo = get_qubo(model)
        eigenvalues, eigenvectors = np.linalg.eigh(qubo)

        return QuboSpectralAnalysisFeatureResult(
            # Eigenvalue
            mean_eigenvalue=NumpyStatsHelper.mean(eigenvalues),
            median_eigenvalue=NumpyStatsHelper.median(eigenvalues),
            std_eigenvalue=NumpyStatsHelper.std(eigenvalues),
            vc_eigenvalue=NumpyStatsHelper.vc(eigenvalues),
            q90_eigenvalue=NumpyStatsHelper.q90(eigenvalues),
            q10_eigenvalue=NumpyStatsHelper.q10(eigenvalues),
            minimum_eigenvalue=NumpyStatsHelper.min(eigenvalues),
            maximum_eigenvalue=NumpyStatsHelper.max(eigenvalues),
            dominant_eigenvalue=NumpyStatsHelper.max(np.abs(eigenvalues)),
            # Eigenvector
            mean_eigenvector=NumpyStatsHelper.mean(eigenvectors),
            median_eigenvector=NumpyStatsHelper.median(eigenvectors),
            std_eigenvector=NumpyStatsHelper.std(eigenvectors),
            vc_eigenvector=NumpyStatsHelper.vc(eigenvectors),
            q90_eigenvector=NumpyStatsHelper.q90(eigenvectors),
            q10_eigenvector=NumpyStatsHelper.q10(eigenvectors),
            minimum_eigenvector=NumpyStatsHelper.min(eigenvectors),
            maximum_eigenvector=NumpyStatsHelper.max(eigenvectors),
            dominant_eigenvector=NumpyStatsHelper.max(np.abs(eigenvectors)),
            # More
            condition_number=np.linalg.cond(qubo),
        )
