from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature
from luna_quantum import Vtype

from .utils import constraint_matrix, mean, vc

if TYPE_CHECKING:
    from luna_quantum import Model


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
        Ac, bc = constraint_matrix(model, degree=1, vtype=Vtype.Real, include_b=True)
        Ac_vnd = np.sum(Ac, axis=0)  # Variable coefficient sums
        Ac_cnd = np.sum(Ac, axis=1)  # Constraint coefficient sums
        Ac_norm = self._normalized_constraint_matrix_entries(Ac, bc)
        Ac_vcs = self._vc_absolute_normalized_constraint_matrix_entries(Ac)

        # Non-continuous
        Anc, bnc = constraint_matrix(
            model, degree=1, vtype=[Vtype.Integer, Vtype.Binary], include_b=True
        )
        Anc_vnd = np.sum(Anc, axis=0)
        Anc_cnd = np.sum(Anc, axis=1)
        Anc_norm = self._normalized_constraint_matrix_entries(Anc, bnc)
        Anc_vcs = self._vc_absolute_normalized_constraint_matrix_entries(Anc)

        # All variables
        Av, bv = constraint_matrix(model, degree=1, vtype=None, include_b=True)
        Av_vnd = np.sum(Av, axis=0)
        Av_cnd = np.sum(Av, axis=1)
        Av_norm = self._normalized_constraint_matrix_entries(Av, bv)
        Av_vcs = self._vc_absolute_normalized_constraint_matrix_entries(Av)

        return LinearConstraintMatrixFeaturesResult(
            # Variable coefficient statistics - continuous
            mean_variable_coefficient_continuous=mean(Ac_vnd),
            vc_variable_coefficient_continuous=vc(Ac_vnd),
            # Variable coefficient statistics - non-continuous
            mean_variable_coefficient_non_continuous=mean(Anc_vnd),
            vc_variable_coefficient_non_continuous=vc(Anc_vnd),
            # Variable coefficient statistics - all
            mean_variable_coefficient_all=mean(Av_vnd),
            vc_variable_coefficient_all=vc(Av_vnd),
            # Constraint coefficient statistics - continuous
            mean_constraint_coefficient_continuous=mean(Ac_cnd),
            vc_constraint_coefficient_continuous=vc(Ac_cnd),
            # Constraint coefficient statistics - non-continuous
            mean_constraint_coefficient_non_continuous=mean(Anc_cnd),
            vc_constraint_coefficient_non_continuous=vc(Anc_cnd),
            # Constraint coefficient statistics - all
            mean_constraint_coefficient=mean(Av_cnd),
            vc_constraint_coefficient=vc(Av_cnd),
            # Distribution of normalized constraint matrix entries - continuous
            mean_distribution_of_normalized_constraint_matrix_entries_continuous=mean(Ac_norm),
            vc_distribution_of_normalized_constraint_matrix_entries_continuous=vc(Ac_norm),
            # Distribution of normalized constraint matrix entries - non-continuous
            mean_distribution_of_normalized_constraint_matrix_entries_non_continuous=mean(Anc_norm),
            vc_distribution_of_normalized_constraint_matrix_entries_non_continuous=vc(Anc_norm),
            # Distribution of normalized constraint matrix entries - all
            mean_distribution_of_normalized_constraint_matrix_entries=mean(Av_norm),
            vc_distribution_of_normalized_constraint_matrix_entries=vc(Av_norm),
            # Variation coefficient of normalized absolute non-zero entries per row - continuous
            mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous=mean(Ac_vcs),
            vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_continuous=vc(Ac_vcs),
            # Variation coefficient of normalized absolute non-zero entries per row - non-continuous
            mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous=mean(Anc_vcs),
            vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row_non_continuous=vc(Anc_vcs),
            # Variation coefficient of normalized absolute non-zero entries per row - all
            mean_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row=mean(Av_vcs),
            vc_variation_coefficient_of_normalized_absolute_non_zero_entries_per_row=vc(Av_vcs),
        )

    def _normalized_constraint_matrix_entries(self, A: NDArray, b: NDArray) -> NDArray:
        """
        Normalize constraint matrix entries by dividing by RHS values.

        Computes A_(i,j) / b_i where b_i != 0.

        Parameters
        ----------
        A : NDArray
            Constraint matrix.
        b : NDArray
            Right-hand side vector.

        Returns
        -------
        NDArray
            Flattened array of normalized entries.
        """
        b_mask = b != 0
        A_nz = A[b_mask, :]
        b_nz = b[b_mask]
        return (A_nz / b_nz[:, None]).flatten()

    def _vc_absolute_normalized_constraint_matrix_entries(self, A: NDArray) -> NDArray:
        """
        Calculate variation coefficient of row-normalized absolute entries.

        The normalization is by dividing by sum of the row's absolute values.

        Parameters
        ----------
        A : NDArray
            Constraint matrix.

        Returns
        -------
        NDArray
            Array of variation coefficients per row.
        """
        vcs = []
        A_rs = np.sum(np.abs(A), axis=1)
        for i in range(A.shape[0]):
            row = A[i, :]
            row_mask = row != 0
            if np.any(row_mask) and A_rs[i] != 0:
                e_nonzero_normed = row[row_mask] / A_rs[i]
                vcs.append(vc(e_nonzero_normed))
        return np.array(vcs)