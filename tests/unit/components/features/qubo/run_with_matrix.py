from typing import TypeVar, overload
from unittest.mock import MagicMock, patch

import numpy as np
from numpy.typing import NDArray

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.components.features.qubo.graph_features import (
    QuboGraphFeature,
    QuboGraphFeatureResult,
)
from luna_bench.components.features.qubo.matrix_features import (
    QuboMatrixFeature,
    QuboMatrixFeatureResult,
)
from luna_bench.components.features.qubo.sparsity_density_features import (
    QuboSparsityDensityFeature,
    QuboSparsityDensityFeatureResult,
)
from luna_bench.components.features.qubo.spectral_analysis_features import (
    QuboSpectralAnalysisFeature,
    QuboSpectralAnalysisFeatureResult,
)

TResult = TypeVar("TResult", bound=ArbitraryDataDomain)


@overload
def run_with_matrix(matrix: NDArray[np.float64], feature: QuboGraphFeature) -> QuboGraphFeatureResult: ...
@overload
def run_with_matrix(matrix: NDArray[np.float64], feature: QuboMatrixFeature) -> QuboMatrixFeatureResult: ...
@overload
def run_with_matrix(
    matrix: NDArray[np.float64], feature: QuboSparsityDensityFeature
) -> QuboSparsityDensityFeatureResult: ...
@overload
def run_with_matrix(
    matrix: NDArray[np.float64], feature: QuboSpectralAnalysisFeature
) -> QuboSpectralAnalysisFeatureResult: ...


def run_with_matrix(matrix: NDArray[np.float64], feature: BaseFeature) -> ArbitraryDataDomain:
    """Run a QUBO feature extractor with a mocked model and QUBO matrix.

    Parameters
    ----------
    matrix : NDArray[np.float64]
        The QUBO matrix to use for feature extraction.
    feature : BaseFeature
        The feature extractor instance to run.

    Returns
    -------
    ArbitraryDataDomain
        The feature extraction result, with type inferred from the feature parameter.
    """
    mock_model = MagicMock()

    # Patch get_qubo in the feature's module
    feature_module = feature.__class__.__module__
    patch_target = f"{feature_module}.get_qubo"

    with patch(patch_target, return_value=matrix):
        return feature.run(mock_model)
