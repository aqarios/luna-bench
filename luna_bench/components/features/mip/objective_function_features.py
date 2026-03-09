from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from luna_model import Variable, Vtype
from pydantic import BaseModel

from luna_bench.base_components import BaseFeature
from luna_bench.components.features.enum_feature_result import EnumFeatureResult
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.components.helper.var_scope import VarScope
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from collections.abc import Callable

    from luna_model import Model
    from numpy.typing import NDArray


class NormType(StrEnum):
    """Type of normalization applied to objective coefficients."""

    ABSOLUTE = "absolute"  # Raw absolute coefficients |c_j|
    NORMALIZED = "normalized"  # |c_j| / count_non_zero(A_j)
    SQRT_NORMALIZED = "sqrt_normalized"  # |c_j| / sqrt(count_non_zero(A_j))


class ObjCoefStatsKey(NamedTuple):
    """
    Key for accessing objective coefficient statistics.

    Attributes
    ----------
    norm_type : NormType
        The type of normalization (ABSOLUTE, NORMALIZED, or SQRT_NORMALIZED).
    var_scope : VarScope
        The scope of variables (CONTINUOUS, NON_CONTINUOUS, or ALL).
    """

    norm_type: NormType
    var_scope: VarScope


class ObjCoefStats(BaseModel):
    """
    Container for objective coefficient statistics.

    Attributes
    ----------
    mean : float
        Mean value of the coefficients.
    std : float
        Standard deviation of the coefficients.
    """

    mean: float
    std: float


class ObjectiveFunctionFeatureResult(EnumFeatureResult[ObjCoefStatsKey, ObjCoefStats]):
    """
    Result container for objective function feature calculations.

    Example
    -------
    .. code-block:: python

        from luna_bench.components.features.mip.objective_function_features import (
            NormType,
            ObjCoefStatsKey,
            ObjectiveFunctionFeature,
            VarScope,
        )

        result = ObjectiveFunctionFeature().run(model)
        obj_stats = result.get(ObjCoefStatsKey(norm_type=NormType.ABSOLUTE, var_scope=VarScope.CONTINUOUS))
        obj_stats.mean
        obj_stats.std
    """


@feature
class ObjectiveFunctionFeature(BaseFeature):
    """
    Feature extractor for objective function coefficient statistics.

    Extracts statistical features (mean, std) of objective function coefficients
    for continuous, non-continuous, and all variable types. Includes raw absolute
    values as well as normalized and square-root-normalized versions.
    """

    def run(self, model: Model) -> ObjectiveFunctionFeatureResult:
        """
        Calculate statistical features of objective function coefficients.

        Computes mean and standard deviation of absolute objective function coefficients
        for continuous, non-continuous, and all variable types. Also calculates these
        statistics for normalized and square-root-normalized coefficient values.

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        ObjectiveFunctionFeatureResult
            Container with statistical measures of objective function coefficients.
        """
        obj_result = ObjectiveFunctionFeatureResult()

        # Get absolute coefficients for each variable scope
        abs_coefs, indices = self._abs_coefficients(model)

        # Define scope configurations
        scope_configs: list[tuple[VarScope, Vtype | list[Vtype] | None]] = [
            (VarScope.CONTINUOUS, Vtype.REAL),
            (VarScope.NON_CONTINUOUS, [Vtype.INTEGER, Vtype.BINARY]),
            (VarScope.ALL, None),
        ]

        # Define normalization configurations
        norm_configs: list[tuple[NormType, Callable[[NDArray[np.float64]], NDArray[np.float64]]]] = [
            (NormType.ABSOLUTE, np.ones_like),  # No normalization (divide by 1)
            (NormType.NORMALIZED, lambda x: x),  # Divide by nnz
            (NormType.SQRT_NORMALIZED, np.sqrt),  # Divide by sqrt(nnz)
        ]

        for var_scope, vtype in scope_configs:
            # Get constraint matrix for this variable scope
            a, _ = ModelMatrix.constraint_matrix(model, degree=int(ConstraintDegree.LINEAR), vtype=vtype)

            coefs = abs_coefs[var_scope]
            var_indices = indices[var_scope]

            for norm_type, norm_func in norm_configs:
                if norm_type == NormType.ABSOLUTE:
                    # For absolute, just use raw coefficients
                    normalized_coefs = coefs
                else:
                    # Apply normalization
                    normalized_coefs = self._normalize(a, coefs, var_indices, norm_func)

                key = ObjCoefStatsKey(norm_type=norm_type, var_scope=var_scope)
                obj_result.add(
                    enum_key=key,
                    value=ObjCoefStats(
                        mean=NumpyStatsHelper.mean(normalized_coefs),
                        std=NumpyStatsHelper.std(normalized_coefs),
                    ),
                )

        return obj_result

    def _normalize(
        self,
        a: NDArray[np.float64],
        coefs: NDArray[np.float64],
        var_indices: list[int],
        f: Callable[[NDArray[np.float64]], NDArray[np.float64]] = lambda x: x,
    ) -> NDArray[np.float64]:
        """
        Normalize coefficients by the (transformed) count of non-zeros in constraint columns.

        Parameters
        ----------
        a : NDArray
            Constraint matrix.
        coefs : NDArray
            Absolute objective coefficients.
        var_indices : list[int]
            Indices of variables in the coefficient array.
        f : Callable
            Transformation function to apply to non-zero counts (e.g., sqrt).

        Returns
        -------
        NDArray
            Normalized coefficients.
        """
        nonzeros = f(np.count_nonzero(a[:, var_indices], axis=0))

        if any(nonzeros == 0):
            return np.zeros_like(nonzeros, dtype=np.float64)
        return coefs / nonzeros

    def _abs_coefficients(self, model: Model) -> tuple[dict[VarScope, NDArray[np.float64]], dict[VarScope, list[int]]]:
        """
        Extract absolute objective coefficients grouped by variable scope.

        Parameters
        ----------
        model : Model
            The optimization model.

        Returns
        -------
        tuple[Dict[VarScope, NDArray], Dict[VarScope, list[int]]]
            Tuple of (coefficients dict, indices dict) keyed by VarScope.
        """
        d_coefs_c: dict[Variable, float] = {}
        d_coefs_nc: dict[Variable, float] = {}
        d_coefs_v: dict[Variable, float] = {}

        for var, v in model.objective.linear_items():
            match var.vtype:
                case Vtype.BINARY | Vtype.INTEGER:
                    d_coefs_nc[var] = v
                    d_coefs_v[var] = v
                case Vtype.REAL:
                    d_coefs_c[var] = v
                    d_coefs_v[var] = v

        vars_c = list(d_coefs_c.keys())
        vars_nc = list(d_coefs_nc.keys())
        vars_v = list(d_coefs_v.keys())

        coefs = {
            VarScope.CONTINUOUS: np.abs([d_coefs_c[var] for var in vars_c]),
            VarScope.NON_CONTINUOUS: np.abs([d_coefs_nc[var] for var in vars_nc]),
            VarScope.ALL: np.abs([d_coefs_v[var] for var in vars_v]),
        }

        # Indices are relative to their own filtered lists
        indices = {
            VarScope.CONTINUOUS: list(range(len(vars_c))),
            VarScope.NON_CONTINUOUS: list(range(len(vars_nc))),
            VarScope.ALL: list(range(len(vars_v))),
        }

        return coefs, indices
