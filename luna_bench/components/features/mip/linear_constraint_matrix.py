from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature

from luna_bench.components.features.utils import constraint_matrix, mean, vc

if TYPE_CHECKING:
    from luna_quantum import Model
    from numpy.typing import NDArray


class LinearConstraintMatrixFeaturesResult(ArbitraryDataDomain):
    """
    Result container for linear constraint matrix feature calculations.

    This class stores statistical measures of linear constraint matrix properties,
    including variable and constraint coefficients, normalized matrix entries,
    and variation coefficients for different variable types.

    Attributes
    ----------
    mean_variable_coefficient_continuous : float
        Mean of variable coefficients for continuous variables.
    vc_variable_coefficient_continuous : float
        Variation coefficient of variable coefficients for continuous variables.
    mean_variable_coefficient_non_continuous : float
        Mean of variable coefficients for non-continuous variables.
    vc_variable_coefficient_non_continuous : float
        Variation coefficient of variable coefficients for non-continuous variables.
    mean_variable_coefficient_all : float
        Mean of variable coefficients for all variables.
    vc_variable_coefficient_all : float
        Variation coefficient of variable coefficients for all variables.
    mean_constraint_coefficient_continuous : float
        Mean of constraint coefficients for continuous constraints.
    vc_constraint_coefficient_continuous : float
        Variation coefficient of constraint coefficients for continuous constraints.
    mean_constraint_coefficient_non_continuous : float
        Mean of constraint coefficients for non-continuous constraints.
    vc_constraint_coefficient_non_continuous : float
        Variation coefficient of constraint coefficients for non-continuous constraints.
    mean_constraint_coefficient : float
        Mean of constraint coefficients for all constraints.
    vc_constraint_coefficient : float
        Variation coefficient of constraint coefficients for all constraints.
    mean_distribution_of_normalized_constraint_matrix_entries_continuous : float
        Mean of normalized constraint matrix entries for continuous variables.
    vc_distribution_of_normalized_constraint_matrix_entries_continuous : float
        Variation coefficient of normalized entries for continuous variables.
    mean_distribution_of_normalized_constraint_matrix_entries_non_continuous : float
        Mean of normalized constraint matrix entries for non-continuous variables.
    vc_distribution_of_normalized_constraint_matrix_entries_non_continuous : float
        Variation coefficient of normalized entries for non-continuous variables.
    mean_distribution_of_normalized_constraint_matrix_entries : float
        Mean of normalized constraint matrix entries for all variables.
    vc_distribution_of_normalized_constraint_matrix_entries : float
        Variation coefficient of normalized entries for all variables.
    mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous : float
        Mean variation coefficient of row-normalized absolute non-zero entries for continuous variables.
    vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous : float
        Variation coefficient of the variation coefficients for continuous variables.
    mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous : float
        Mean variation coefficient of row-normalized absolute non-zero entries for non-continuous variables.
    vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous : float
        Variation coefficient of the variation coefficients for non-continuous variables.
    mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row : float
        Mean variation coefficient of row-normalized absolute non-zero entries for all variables.
    vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row : float
        Variation coefficient of the variation coefficients for all variables.
    """

    # Variable coefficient statistics - continuous
    mean_variable_coefficient_continuous: float
    vc_variable_coefficient_continuous: float

    # Variable coefficient statistics - non-continuous
    mean_variable_coefficient_non_continuous: float
    vc_variable_coefficient_non_continuous: float

    # Variable coefficient statistics - all
    mean_variable_coefficient_all: float
    vc_variable_coefficient_all: float

    # Constraint coefficient statistics - continuous
    mean_constraint_coefficient_continuous: float
    vc_constraint_coefficient_continuous: float

    # Constraint coefficient statistics - non-continuous
    mean_constraint_coefficient_non_continuous: float
    vc_constraint_coefficient_non_continuous: float

    # Constraint coefficient statistics - all
    mean_constraint_coefficient: float
    vc_constraint_coefficient: float

    # Distribution of normalized constraint matrix entries - continuous
    mean_distribution_of_normalized_constraint_matrix_entries_continuous: float
    vc_distribution_of_normalized_constraint_matrix_entries_continuous: float

    # Distribution of normalized constraint matrix entries - non-continuous
    mean_distribution_of_normalized_constraint_matrix_entries_non_continuous: float
    vc_distribution_of_normalized_constraint_matrix_entries_non_continuous: float

    # Distribution of normalized constraint matrix entries - all
    mean_distribution_of_normalized_constraint_matrix_entries: float
    vc_distribution_of_normalized_constraint_matrix_entries: float

    # Variation coefficient of normalized absolute non-zero entries per row - continuous
    mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous: float
    vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous: float

    # Variation coefficient of normalized absolute non-zero entries per row - non-continuous
    mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous: float
    vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous: float

    # Variation coefficient of normalized absolute non-zero entries per row - all
    mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row: float
    vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row: float


@feature
class LinearConstraintMatrixFeatures(IFeature):
    """
    Feature extractor for linear constraint matrix properties.

    Extracts statistical features related to variable coefficients, constraint
    coefficients, and the distribution of constraint matrix entries. Includes
    both continuous and non-continuous features, as well as normalized and
    variation coefficient metrics.
    """

    def run(self, model: Model) -> ArbitraryDataDomain:
        """
        Calculate linear constraint matrix features.

        Computes various statistics for the constraint matrix including coefficient
        sums, normalized entries, and variation coefficients, grouped by variable type.

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        LinearConstraintMatrixFeaturesResult
            Container with constraint matrix statistical measures.
        """
        # Continuous
        ac, bc = constraint_matrix(model, degree=1, vtype=Vtype.Real, include_b=True)
        ac_vnd = np.sum(ac, axis=0)  # Variable coefficient sums
        ac_cnd = np.sum(ac, axis=1)  # Constraint coefficient sums
        ac_norm = self._normalized_constraint_matrix_entries(ac, bc)
        ac_vcs = self._vc_absolute_normalized_constraint_matrix_entries(ac)

        # Non-continuous
        anc, bnc = constraint_matrix(model, degree=1, vtype=[Vtype.Integer, Vtype.Binary], include_b=True)
        anc_vnd = np.sum(anc, axis=0)
        anc_cnd = np.sum(anc, axis=1)
        anc_norm = self._normalized_constraint_matrix_entries(anc, bnc)
        anc_vcs = self._vc_absolute_normalized_constraint_matrix_entries(anc)

        # all variables
        av, bv = constraint_matrix(model, degree=1, vtype=None, include_b=True)
        av_vnd = np.sum(av, axis=0)
        av_cnd = np.sum(av, axis=1)
        av_norm = self._normalized_constraint_matrix_entries(av, bv)
        av_vcs = self._vc_absolute_normalized_constraint_matrix_entries(av)

        return LinearConstraintMatrixFeaturesResult(
            # Variable coefficient statistics - continuous
            mean_variable_coefficient_continuous=mean(ac_vnd),
            vc_variable_coefficient_continuous=vc(ac_vnd),
            # Variable coefficient statistics - non-continuous
            mean_variable_coefficient_non_continuous=mean(anc_vnd),
            vc_variable_coefficient_non_continuous=vc(anc_vnd),
            # Variable coefficient statistics - all
            mean_variable_coefficient_all=mean(av_vnd),
            vc_variable_coefficient_all=vc(av_vnd),
            # Constraint coefficient statistics - continuous
            mean_constraint_coefficient_continuous=mean(ac_cnd),
            vc_constraint_coefficient_continuous=vc(ac_cnd),
            # Constraint coefficient statistics - non-continuous
            mean_constraint_coefficient_non_continuous=mean(anc_cnd),
            vc_constraint_coefficient_non_continuous=vc(anc_cnd),
            # Constraint coefficient statistics - all
            mean_constraint_coefficient=mean(av_cnd),
            vc_constraint_coefficient=vc(av_cnd),
            # Distribution of normalized constraint matrix entries - continuous
            mean_distribution_of_normalized_constraint_matrix_entries_continuous=mean(ac_norm),
            vc_distribution_of_normalized_constraint_matrix_entries_continuous=vc(ac_norm),
            # Distribution of normalized constraint matrix entries - non-continuous
            mean_distribution_of_normalized_constraint_matrix_entries_non_continuous=mean(anc_norm),
            vc_distribution_of_normalized_constraint_matrix_entries_non_continuous=vc(anc_norm),
            # Distribution of normalized constraint matrix entries - all
            mean_distribution_of_normalized_constraint_matrix_entries=mean(av_norm),
            vc_distribution_of_normalized_constraint_matrix_entries=vc(av_norm),
            # Variation coefficient of normalized absolute non-zero entries per row - continuous
            mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous=mean(ac_vcs),
            vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous=vc(ac_vcs),
            # Variation coefficient of normalized absolute non-zero entries per row - non-continuous
            mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous=mean(anc_vcs),
            vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous=vc(anc_vcs),
            # Variation coefficient of normalized absolute non-zero entries per row - all
            mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row=mean(av_vcs),
            vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row=vc(av_vcs),
        )

    def _normalized_constraint_matrix_entries(self, a: NDArray, b: NDArray) -> NDArray:
        """
        Normalize constraint matrix entries by dividing by RHS values.

        Computes a_(i,j) / b_i where b_i != 0.

        Parameters
        ----------
        a : NDArray
            Constraint matrix.
        b : NDArray
            Right-hand side vector.

        Returns
        -------
        NDArray
            Flattened array of normalized entries.
        """
        b_mask = b != 0
        a_nz = a[b_mask, :]
        b_nz = b[b_mask]
        return (a_nz / b_nz[:, None]).flatten()

    def _vc_absolute_normalized_constraint_matrix_entries(self, a: NDArray) -> NDArray:
        """
        Calculate variation coefficient of row-normalized absolute entries.

        The normalization is by dividing by sum of the row's absolute values.

        Parameters
        ----------
        a : NDArray
            Constraint matrix.

        Returns
        -------
        NDArray
            array of variation coefficients per row.
        """
        vcs = []
        a_rs = np.sum(np.abs(a), axis=1)
        for i in range(a.shape[0]):
            row = a[i, :]
            row_mask = row != 0
            if np.any(row_mask) and a_rs[i] != 0:
                e_nonzero_normed = row[row_mask] / a_rs[i]
                vcs.append(vc(e_nonzero_normed))
        return np.array(vcs)
