from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype
from pydantic import BaseModel

from luna_bench._internal.interfaces import IFeature
from luna_bench.components.features.base_results import BaseStatsResultWithVarScope
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.components.helper.var_scope import VarScope
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model
    from numpy.typing import NDArray


class CoefType(str, Enum):
    """Type of coefficient being measured."""

    VARIABLE = "variable"  # Sum over constraints (column-wise sum of A)
    CONSTRAINT = "constraint"  # Sum over variables (row-wise sum of A)
    NORMALIZED = "normalized"  # Normalized matrix entries: a_ij / b_i
    ROW_VARIATION = "row_variation"  # VC of row-normalized absolute non-zero entries


class CoefStats(BaseModel):
    """
    Container for coefficient statistics with descriptive context.

    Attributes
    ----------
    coef_type : CoefType
        The type of coefficient being measured (variable, constraint, normalized, row_variation).
    var_scope : VarScope
        The scope of variables included (continuous, non_continuous, all).
    mean : float
        Mean value of the coefficients.
    variation_coefficient : float
        Variation coefficient (std/mean) of the coefficients.
    """

    coef_type: CoefType
    var_scope: VarScope
    mean: float
    variation_coefficient: float


class LinearConstraintMatrixFeaturesResult(BaseStatsResultWithVarScope[CoefType, CoefStats]):
    """
    Result container for linear constraint matrix feature calculations.

    This class stores statistical measures of linear constraint matrix properties,
    including variable and constraint coefficients, normalized matrix entries,
    and variation coefficients for different variable types.

    Access patterns:
        - result.get(CoefType.VARIABLE, VarScope.CONTINUOUS) -> CoefStats
        - result.get_mean(CoefType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.get_vc(CoefType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.by_type(CoefType.VARIABLE) -> Dict[VarScope, CoefStats]
        - result.by_scope(VarScope.CONTINUOUS) -> Dict[CoefType, CoefStats]

    Attributes
    ----------
    stats : Dict[str, CoefStats]
        Dictionary mapping "{coef_type}_{var_scope}" keys to CoefStats objects.
    """

    @staticmethod
    def _type_enum() -> type[CoefType]:
        """Return the CoefType enum class."""
        return CoefType

    def get_vc(self, coef_type: CoefType, var_scope: VarScope) -> float:
        """Direct access to variation coefficient."""
        return self.get(coef_type, var_scope).variation_coefficient


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
        stats: dict[str, CoefStats] = {}

        # Define the variable type configurations
        scope_configs = [
            (VarScope.CONTINUOUS, Vtype.Real),
            (VarScope.NON_CONTINUOUS, [Vtype.Integer, Vtype.Binary]),
            (VarScope.ALL, None),
        ]

        for var_scope, vtype in scope_configs:
            # Get constraint matrix for this variable scope
            a, b = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=vtype, include_b=True)

            # Variable coefficients (column sums)
            var_coef = np.sum(a, axis=0)
            stats[LinearConstraintMatrixFeaturesResult.make_key(CoefType.VARIABLE, var_scope)] = CoefStats(
                coef_type=CoefType.VARIABLE,
                var_scope=var_scope,
                mean=NumpyStatsHelper.mean(var_coef),
                variation_coefficient=NumpyStatsHelper.vc(var_coef),
            )

            # Constraint coefficients (row sums)
            cons_coef = np.sum(a, axis=1)
            stats[LinearConstraintMatrixFeaturesResult.make_key(CoefType.CONSTRAINT, var_scope)] = CoefStats(
                coef_type=CoefType.CONSTRAINT,
                var_scope=var_scope,
                mean=NumpyStatsHelper.mean(cons_coef),
                variation_coefficient=NumpyStatsHelper.vc(cons_coef),
            )

            # Normalized matrix entries (a_ij / b_i)
            norm_entries = self._norm_cons_matrix_entr(a, b)
            stats[LinearConstraintMatrixFeaturesResult.make_key(CoefType.NORMALIZED, var_scope)] = CoefStats(
                coef_type=CoefType.NORMALIZED,
                var_scope=var_scope,
                mean=NumpyStatsHelper.mean(norm_entries),
                variation_coefficient=NumpyStatsHelper.vc(norm_entries),
            )

            # Row variation coefficients
            row_vcs = self._vc_abs_norm_cons_matrix_entr(a)
            stats[LinearConstraintMatrixFeaturesResult.make_key(CoefType.ROW_VARIATION, var_scope)] = CoefStats(
                coef_type=CoefType.ROW_VARIATION,
                var_scope=var_scope,
                mean=NumpyStatsHelper.mean(row_vcs),
                variation_coefficient=NumpyStatsHelper.vc(row_vcs),
            )

        return LinearConstraintMatrixFeaturesResult(stats=stats)

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
            Array of variation coefficients per row.
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
