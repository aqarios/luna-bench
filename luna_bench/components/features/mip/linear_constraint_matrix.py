from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model
    from numpy.typing import NDArray

from pydantic import BaseModel


class CoefStats(BaseModel):
    """Container for coefficient statistics."""

    coef_mean: float
    coef_vc: float


class LinearConstraintMatrixFeaturesResult(ArbitraryDataDomain):
    """
    Result container for linear constraint matrix feature calculations.

    This class stores statistical measures of linear constraint matrix properties,
    including variable and constraint coefficients, normalized matrix entries,
    and variation coefficients for different variable types.

    Attributes
    ----------
    mean_var_coef_cont : float
        Mean of variable coefficients for continuous variables.
    vc_var_coef_cont : float
        Variation coefficient of variable coefficients for continuous variables.
    mean_var_coef_non_cont : float
        Mean of variable coefficients for non-continuous variables.
    vc_var_coef_non_cont : float
        Variation coefficient of variable coefficients for non-continuous variables.
    mean_var_coef_all : float
        Mean of variable coefficients for all variables.
    vc_var_coef_all : float
        Variation coefficient of variable coefficients for all variables.
    mean_cons_coef_cont : float
        Mean of constraint coefficients for continuous constraints.
    vc_cons_coef_cont : float
        Variation coefficient of constraint coefficients for continuous constraints.
    mean_cons_coef_non_cont : float
        Mean of constraint coefficients for non-continuous constraints.
    vc_cons_coef_non_cont : float
        Variation coefficient of constraint coefficients for non-continuous constraints.
    mean_cons_coefficient : float
        Mean of constraint coefficients for all constraints.
    vc_cons_coefficient : float
        Variation coefficient of constraint coefficients for all constraints.
    mean_dist_of_norm_cons_matrix_entr_cont : float
        Mean of normalized constraint matrix entries for continuous variables.
    vc_dist_of_norm_cons_matrix_entr_cont : float
        Variation coefficient of normalized entries for continuous variables.
    mean_dist_of_norm_cons_matrix_entr_non_cont : float
        Mean of normalized constraint matrix entries for non-continuous variables.
    vc_dist_of_norm_cons_matrix_entr_non_cont : float
        Variation coefficient of normalized entries for non-continuous variables.
    mean_dist_of_norm_cons_matrix_entr : float
        Mean of normalized constraint matrix entries for all variables.
    vc_dist_of_norm_cons_matrix_entr : float
        Variation coefficient of normalized entries for all variables.
    mean_vari_coef_of_norm_abs_non_zero_entr_per_row_cont : float
        Mean variation coefficient of row-normalized absolute non-zero entries for continuous variables.
    vc_vari_coef_of_norm_abs_non_zero_entr_per_row_cont : float
        Variation coefficient of the variation coefficients for continuous variables.
    mean_vari_coef_of_norm_abs_non_zero_entr_per_row_non_cont : float
        Mean variation coefficient of row-normalized absolute non-zero entries for non-continuous variables.
    vc_vari_coef_of_norm_abs_non_zero_entr_per_row_non_cont : float
        Variation coefficient of the variation coefficients for non-continuous variables.
    mean_vari_coef_of_norm_abs_non_zero_entr_per_row : float
        Mean variation coefficient of row-normalized absolute non-zero entries for all variables.
    vc_vari_coef_of_norm_abs_non_zero_entr_per_row : float
        Variation coefficient of the variation coefficients for all variables.
    """

    mean_var_coef_cont: float
    vc_var_coef_cont: float

    mean_var_coef_non_cont: float
    vc_var_coef_non_cont: float

    mean_var_coef_all: float
    vc_var_coef_all: float

    mean_cons_coef_cont: float
    vc_cons_coef_cont: float

    mean_cons_coef_non_cont: float
    vc_cons_coef_non_cont: float

    mean_cons_coefficient: float
    vc_cons_coefficient: float

    mean_dist_of_norm_cons_matrix_entr_cont: float
    vc_dist_of_norm_cons_matrix_entr_cont: float

    mean_dist_of_norm_cons_matrix_entr_non_cont: float
    vc_dist_of_norm_cons_matrix_entr_non_cont: float

    mean_dist_of_norm_cons_matrix_entr: float
    vc_dist_of_norm_cons_matrix_entr: float

    mean_vari_coef_of_norm_abs_non_zero_entr_per_row_cont: float
    vc_vari_coef_of_norm_abs_non_zero_entr_per_row_cont: float

    mean_vari_coef_of_norm_abs_non_zero_entr_per_row_non_cont: float
    vc_vari_coef_of_norm_abs_non_zero_entr_per_row_non_cont: float

    mean_vari_coef_of_norm_abs_non_zero_entr_per_row: float
    vc_vari_coef_of_norm_abs_non_zero_entr_per_row: float


@feature
class LinearConstraintMatrixFeatures(IFeature):
    """
    Feature extractor for linear constraint matrix properties.

    Extracts statistical features related to variable coefficients, constraint
    coefficients, and the distribution of constraint matrix entries. Includes
    both continuous and non-continuous features, as well as normalized and
    variation coefficient metrics.
    """

    def run(self, model: Model) -> LinearConstraintMatrixFeaturesResult:
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
        ac, bc = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=Vtype.Real, include_b=True)
        ac_vnd = np.sum(ac, axis=0)
        ac_cnd = np.sum(ac, axis=1)
        ac_norm = self._norm_cons_matrix_entr(ac, bc)
        ac_vcs = self._vc_abs_norm_cons_matrix_entr(ac)

        # Non-continuous
        anc, bnc = ModelMatrix.constraint_matrix(
            model, degree=ConstraintDegree.LINEAR, vtype=[Vtype.Integer, Vtype.Binary], include_b=True
        )
        anc_vnd = np.sum(anc, axis=0)
        anc_cnd = np.sum(anc, axis=1)
        anc_norm = self._norm_cons_matrix_entr(anc, bnc)
        anc_vcs = self._vc_abs_norm_cons_matrix_entr(anc)

        # all variables
        av, bv = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=None, include_b=True)
        av_vnd = np.sum(av, axis=0)
        av_cnd = np.sum(av, axis=1)
        av_norm = self._norm_cons_matrix_entr(av, bv)
        av_vcs = self._vc_abs_norm_cons_matrix_entr(av)

        return LinearConstraintMatrixFeaturesResult(
            mean_var_coef_cont=NumpyStatsHelper.mean(ac_vnd),
            vc_var_coef_cont=NumpyStatsHelper.vc(ac_vnd),
            mean_var_coef_non_cont=NumpyStatsHelper.mean(anc_vnd),
            vc_var_coef_non_cont=NumpyStatsHelper.vc(anc_vnd),
            mean_var_coef_all=NumpyStatsHelper.mean(av_vnd),
            vc_var_coef_all=NumpyStatsHelper.vc(av_vnd),
            mean_cons_coef_cont=NumpyStatsHelper.mean(ac_cnd),
            vc_cons_coef_cont=NumpyStatsHelper.vc(ac_cnd),
            mean_cons_coef_non_cont=NumpyStatsHelper.mean(anc_cnd),
            vc_cons_coef_non_cont=NumpyStatsHelper.vc(anc_cnd),
            mean_cons_coefficient=NumpyStatsHelper.mean(av_cnd),
            vc_cons_coefficient=NumpyStatsHelper.vc(av_cnd),
            mean_dist_of_norm_cons_matrix_entr_cont=NumpyStatsHelper.mean(ac_norm),
            vc_dist_of_norm_cons_matrix_entr_cont=NumpyStatsHelper.vc(ac_norm),
            mean_dist_of_norm_cons_matrix_entr_non_cont=NumpyStatsHelper.mean(anc_norm),
            vc_dist_of_norm_cons_matrix_entr_non_cont=NumpyStatsHelper.vc(anc_norm),
            mean_dist_of_norm_cons_matrix_entr=NumpyStatsHelper.mean(av_norm),
            vc_dist_of_norm_cons_matrix_entr=NumpyStatsHelper.vc(av_norm),
            mean_vari_coef_of_norm_abs_non_zero_entr_per_row_cont=NumpyStatsHelper.mean(ac_vcs),
            vc_vari_coef_of_norm_abs_non_zero_entr_per_row_cont=NumpyStatsHelper.vc(ac_vcs),
            mean_vari_coef_of_norm_abs_non_zero_entr_per_row_non_cont=NumpyStatsHelper.mean(anc_vcs),
            vc_vari_coef_of_norm_abs_non_zero_entr_per_row_non_cont=NumpyStatsHelper.vc(anc_vcs),
            mean_vari_coef_of_norm_abs_non_zero_entr_per_row=NumpyStatsHelper.mean(av_vcs),
            vc_vari_coef_of_norm_abs_non_zero_entr_per_row=NumpyStatsHelper.vc(av_vcs),
        )

    def _norm_cons_matrix_entr(self, a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
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
        normalized: NDArray[np.float64] = (a_nz / b_nz[:, None]).flatten()
        return normalized

    def _vc_abs_norm_cons_matrix_entr(self, a: NDArray[np.float64]) -> NDArray[np.float64]:
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
                vcs.append(NumpyStatsHelper.vc(e_nonzero_normed))
        return np.array(vcs)
