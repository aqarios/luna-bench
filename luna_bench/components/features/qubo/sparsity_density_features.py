from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.helpers import feature

from .get_qubo import get_qubo

if TYPE_CHECKING:
    from luna_quantum import Model


class QuboSparsityDensityFeatureResult(ArbitraryDataDomain):
    """Result container for sparsity and density QUBO features.

    Attributes
    ----------
    sparsity
        Fraction of zero entries: ``num_zero / total_entries``.
    density
        Fraction of non-zero entries: ``num_non_zero / total_entries``.
        Complement of sparsity (``sparsity + density = 1``).
    num_zero
        Count of zero entries in the matrix.
    num_non_zero
        Count of non-zero entries in the matrix.
    num_variables
        Number of QUBO variables (matrix dimension / number of rows).
    """

    sparsity: float
    density: float
    num_zero: int
    num_non_zero: int
    num_variables: int


@feature
class QuboSparsityDensityFeature(BaseFeature):
    """Extract sparsity and density features from QUBO models.

    Compute structural features describing the fill pattern of the QUBO matrix.

    Extracted features include:

    - **Ratios**: Sparsity and density of the matrix.
    - **Counts**: Number of zero and non-zero entries.
    - **Size**: Number of variables (matrix dimension).
    """

    def run(self, model: Model) -> QuboSparsityDensityFeatureResult:
        """Compute sparsity and density features for the given model.

        Parameters
        ----------
        model : Model
            The optimization model to extract features from.

        Returns
        -------
        QuboSparsityDensityFeatureResult
            A result object containing the computed sparsity/density features.
        """
        qubo = get_qubo(model)
        num_entries = qubo.size
        num_non_zero = np.count_nonzero(qubo)
        num_zero = num_entries - num_non_zero

        sparsity = num_zero / num_entries
        density = num_non_zero / num_entries

        return QuboSparsityDensityFeatureResult(
            sparsity=sparsity,
            density=density,
            num_zero=int(num_zero),
            num_non_zero=int(num_non_zero),
            num_variables=qubo.shape[0],
        )
