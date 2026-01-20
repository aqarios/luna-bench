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
    from collections.abc import Callable

    from luna_quantum import Model
    from numpy.typing import NDArray


class NormType(str, Enum):
    """Type of normalization applied to objective coefficients."""

    ABSOLUTE = "absolute"  # Raw absolute coefficients |c_j|
    NORMALIZED = "normalized"  # |c_j| / nnz(A_j) where nnz = count of non-zeros in column
    SQRT_NORMALIZED = "sqrt_normalized"  # |c_j| / sqrt(nnz(A_j))


class ObjCoefStats(BaseModel):
    """
    Container for objective coefficient statistics with descriptive context.

    Attributes
    ----------
    norm_type : NormType
        The type of normalization applied (absolute, normalized, sqrt_normalized).
    var_scope : VarScope
        The scope of variables included (continuous, non_continuous, all).
    mean : float
        Mean value of the coefficients.
    std : float
        Standard deviation of the coefficients.
    """

    norm_type: NormType
    var_scope: VarScope
    mean: float
    std: float

    @property
    def description(self) -> str:
        """Human-readable description of what this stat represents."""
        norm_desc = {
            NormType.ABSOLUTE: "absolute objective coefficients |c_j|",
            NormType.NORMALIZED: "normalized objective coefficients |c_j| / nnz(A_j)",
            NormType.SQRT_NORMALIZED: "sqrt-normalized objective coefficients |c_j| / sqrt(nnz(A_j))",
        }
        scope_desc = {
            VarScope.CONTINUOUS: "continuous variables only",
            VarScope.NON_CONTINUOUS: "integer/binary variables only",
            VarScope.ALL: "all variables",
        }
        return f"{norm_desc[self.norm_type]} for {scope_desc[self.var_scope]}"


class ObjectiveFunctionFeatureResult(BaseStatsResultWithVarScope[NormType, ObjCoefStats]):
    """
    Result container for objective function feature calculations.

    This class stores statistical measures of objective function coefficients,
    including absolute values and normalized versions using different normalization
    strategies (standard and square-root normalization) across different variable types.

    Access patterns:
        - result.get(NormType.ABSOLUTE, VarScope.CONTINUOUS) -> ObjCoefStats
        - result.get_mean(NormType.ABSOLUTE, VarScope.CONTINUOUS) -> float
        - result.get_std(NormType.ABSOLUTE, VarScope.CONTINUOUS) -> float
        - result.by_type(NormType.ABSOLUTE) -> Dict[VarScope, ObjCoefStats]
        - result.by_scope(VarScope.CONTINUOUS) -> Dict[NormType, ObjCoefStats]

    Attributes
    ----------
    stats : Dict[str, ObjCoefStats]
        Dictionary mapping "{norm_type}_{var_scope}" keys to ObjCoefStats objects.
    """

    @staticmethod
    def _type_enum() -> type[NormType]:
        """Return the NormType enum class."""
        return NormType

    def get_std(self, norm_type: NormType, var_scope: VarScope) -> float:
        """Direct access to standard deviation."""
        return self.get(norm_type, var_scope).std


@feature
class ObjectiveFunctionFeature(IFeature):
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
        stats: dict[str, ObjCoefStats] = {}

        # Get absolute coefficients for each variable scope
        abs_coefs, indices = self._abs_coefficients(model)

        # Define scope configurations
        scope_configs = [
            (VarScope.CONTINUOUS, Vtype.Real),
            (VarScope.NON_CONTINUOUS, [Vtype.Integer, Vtype.Binary]),
            (VarScope.ALL, None),
        ]

        # Define normalization configurations
        norm_configs: list[tuple[NormType, Callable[[NDArray[np.float64]], NDArray[np.float64]]]] = [
            (NormType.ABSOLUTE, lambda x: np.ones_like(x)),  # No normalization (divide by 1)
            (NormType.NORMALIZED, lambda x: x),  # Divide by nnz
            (NormType.SQRT_NORMALIZED, np.sqrt),  # Divide by sqrt(nnz)
        ]

        for var_scope, vtype in scope_configs:
            # Get constraint matrix for this variable scope
            a, _ = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=vtype)

            coefs = abs_coefs[var_scope]
            var_indices = indices[var_scope]

            for norm_type, norm_func in norm_configs:
                if norm_type == NormType.ABSOLUTE:
                    # For absolute, just use raw coefficients
                    normalized_coefs = coefs
                else:
                    # Apply normalization
                    normalized_coefs = self._normalize(a, coefs, var_indices, norm_func)

                key = ObjectiveFunctionFeatureResult.make_key(norm_type, var_scope)
                stats[key] = ObjCoefStats(
                    norm_type=norm_type,
                    var_scope=var_scope,
                    mean=NumpyStatsHelper.mean(normalized_coefs),
                    std=NumpyStatsHelper.std(normalized_coefs),
                )

        return ObjectiveFunctionFeatureResult(stats=stats)

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
        d_coefs_c: dict = {}
        d_coefs_nc: dict = {}
        d_coefs_v: dict = {}

        for var, v in model.objective.linear_items():
            match var.vtype:
                case Vtype.Binary | Vtype.Integer:
                    d_coefs_nc[var] = v
                    d_coefs_v[var] = v
                case Vtype.Real:
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
