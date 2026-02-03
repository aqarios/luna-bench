from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from luna_quantum import Vtype
from pydantic import BaseModel

from luna_bench.base_components import BaseFeature
from luna_bench.components.features.base_feature import BaseFeatureResult
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


class CoefStatsKey(NamedTuple):
    """
    Key for accessing coefficient statistics.

    Attributes
    ----------
    coef_type : CoefType
        The type of coefficient (VARIABLE, CONSTRAINT, NORMALIZED, or ROW_VARIATION).
    var_scope : VarScope
        The scope of variables (CONTINUOUS, NON_CONTINUOUS, or ALL).
    """

    coef_type: CoefType
    var_scope: VarScope

    @property
    def to_key(self) -> str:
        """Function to generate key from NamedTuple."""
        return str(self._asdict())


class CoefStats(BaseModel):
    """
    Container for coefficient statistics with descriptive context.

    Attributes
    ----------
    mean : float
        Mean value of the coefficients.
    variation_coefficient : float
        Variation coefficient (std/mean) of the coefficients.
    """

    mean: float
    variation_coefficient: float


class LinearConstraintMatrixFeaturesResult(BaseFeatureResult[CoefStatsKey, CoefStats]):
    """
    Result container for linear constraint matrix feature calculations.

    Example
    -------
    .. code-block:: python

        from luna_bench.components.features.mip.linear_constraint_matrix import (
            CoefStatsKey,
            CoefType,
            LinearConstraintMatrixFeatures,
        )
        from luna_bench.components.helper.var_scope import VarScope

        result = LinearConstraintMatrixFeatures().run(model)
        coef_stats = result.get(CoefStatsKey(coef_type=CoefType.VARIABLE, var_scope=VarScope.CONTINUOUS))
        coef_stats.mean
        coef_stats.variation_coefficient
    """


@feature
class LinearConstraintMatrixFeatures(BaseFeature):
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
        lin_con_result = LinearConstraintMatrixFeaturesResult()

        # Define the variable type configurations
        scope_configs: list[tuple[VarScope, Vtype | list[Vtype] | None]] = [
            (VarScope.CONTINUOUS, Vtype.Real),
            (VarScope.NON_CONTINUOUS, [Vtype.Integer, Vtype.Binary]),
            (VarScope.ALL, None),
        ]

        for var_scope, vtype in scope_configs:
            # Get constraint matrix for this variable scope
            a, b = ModelMatrix.constraint_matrix(
                model, degree=int(ConstraintDegree.LINEAR), vtype=vtype, include_b=True
            )

            # Variable coefficients (column sums)
            var_coef = np.sum(a, axis=0)
            lin_con_result.add(
                enum_key=CoefStatsKey(coef_type=CoefType.VARIABLE, var_scope=var_scope),
                value=CoefStats(
                    mean=NumpyStatsHelper.mean(var_coef),
                    variation_coefficient=NumpyStatsHelper.vc(var_coef),
                ),
            )

            # Constraint coefficients (row sums)
            cons_coef = np.sum(a, axis=1)
            lin_con_result.add(
                enum_key=CoefStatsKey(coef_type=CoefType.CONSTRAINT, var_scope=var_scope),
                value=CoefStats(
                    mean=NumpyStatsHelper.mean(cons_coef),
                    variation_coefficient=NumpyStatsHelper.vc(cons_coef),
                ),
            )

            # Normalized matrix entries (a_ij / b_i)
            norm_entries = self._norm_cons_matrix_entr(a, b)
            lin_con_result.add(
                enum_key=CoefStatsKey(coef_type=CoefType.NORMALIZED, var_scope=var_scope),
                value=CoefStats(
                    mean=NumpyStatsHelper.mean(norm_entries),
                    variation_coefficient=NumpyStatsHelper.vc(norm_entries),
                ),
            )

            # Row variation coefficients
            row_vcs = self._vc_abs_norm_cons_matrix_entr(a)
            lin_con_result.add(
                enum_key=CoefStatsKey(coef_type=CoefType.ROW_VARIATION, var_scope=var_scope),
                value=CoefStats(
                    mean=NumpyStatsHelper.mean(row_vcs),
                    variation_coefficient=NumpyStatsHelper.vc(row_vcs),
                ),
            )

        return lin_con_result

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
