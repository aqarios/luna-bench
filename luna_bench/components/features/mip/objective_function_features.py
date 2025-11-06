from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature

from luna_bench.components.features.utils import constraint_matrix, mean, std

if TYPE_CHECKING:
    from collections.abc import Callable

    from luna_quantum import Model
    from numpy.typing import NDArray


class ObjectiveFunctionFeatureResult(ArbitraryDataDomain):
    """
    Result container for objective function feature calculations.

    This class stores statistical measures of objective function coefficients,
    including absolute values and normalized versions using different normalization
    strategies (standard and square-root normalization) across different variable types.

    Attributes
    ----------
    mean_abscoefs_c : float
        Mean of absolute objective function coefficients for continuous variables.
    std_abscoefs_c : float
        Standard deviation of absolute objective function coefficients for continuous variables.
    mean_abscoefs_nc : float
        Mean of absolute objective function coefficients for non-continuous variables.
    std_abscoefs_nc : float
        Standard deviation of absolute objective function coefficients for non-continuous variables.
    mean_abscoefs_v : float
        Mean of absolute objective function coefficients for all variables.
    std_abscoefs_v : float
        Standard deviation of absolute objective function coefficients for all variables.
    mean_norm_abscoefs_c : float
        Mean of normalized absolute objective function coefficients for continuous variables.
    std_norm_abscoefs_c : float
        Standard deviation of normalized absolute objective function coefficients for continuous variables.
    mean_norm_abscoefs_nc : float
        Mean of normalized absolute objective function coefficients for non-continuous variables.
    std_norm_abscoefs_nc : float
        Standard deviation of normalized absolute objective function coefficients for non-continuous variables.
    mean_norm_abscoefs_v : float
        Mean of normalized absolute objective function coefficients for all variables.
    std_norm_abscoefs_v : float
        Standard deviation of normalized absolute objective function coefficients for all variables.
    mean_sqrtnorm_abscoefs_c : float
        Mean of square-root-normalized absolute objective function coefficients for continuous variables.
    std_sqrtnorm_abscoefs_c : float
        Standard deviation of square-root-normalized absolute objective function coefficients for continuous variables.
    mean_sqrtnorm_abscoefs_nc : float
        Mean of square-root-normalized absolute objective function coefficients for non-continuous variables.
    std_sqrtnorm_abscoefs_nc : float
        Standard deviation of square-root-normalized absolute objective function coefficients for
        non-continuous variables.
    mean_sqrtnorm_abscoefs_v : float
        Mean of square-root-normalized absolute objective function coefficients for all variables.
    std_sqrtnorm_abscoefs_v : float
        Standard deviation of square-root-normalized absolute objective function coefficients for all variables.
    """

    # absolute objective function coefficients - continuous
    mean_abscoefs_c: float
    std_abscoefs_c: float

    # absolute objective function coefficients - non-continuous
    mean_abscoefs_nc: float
    std_abscoefs_nc: float

    # absolute objective function coefficients - all
    mean_abscoefs_v: float
    std_abscoefs_v: float

    # Normalized absolute objective function coefficients - continuous
    mean_norm_abscoefs_c: float
    std_norm_abscoefs_c: float

    # Normalized absolute objective function coefficients - non-continuous
    mean_norm_abscoefs_nc: float
    std_norm_abscoefs_nc: float

    # Normalized absolute objective function coefficients - all
    mean_norm_abscoefs_v: float
    std_norm_abscoefs_v: float

    # Square-root-normalized absolute objective function coefficients - continuous
    mean_sqrtnorm_abscoefs_c: float
    std_sqrtnorm_abscoefs_c: float

    # Square-root-normalized absolute objective function coefficients - non-continuous
    mean_sqrtnorm_abscoefs_nc: float
    std_sqrtnorm_abscoefs_nc: float

    # Square-root-normalized absolute objective function coefficients - all
    mean_sqrtnorm_abscoefs_v: float
    std_sqrtnorm_abscoefs_v: float


@feature
class ObjectiveFunctionFeature(IFeature):
    """Fake feature class."""

    def run(self, model: Model) -> ArbitraryDataDomain:
        """
        Calculate statistical features of objective function coefficients.

        Computes mean and standard deviation of absolute objective function coefficients
        for continuous, non-continuous, and all variable types. also calculates these
        statistics for normalized and square-root-normalized coefficient values.

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        ObjectiveFunctionFeatureResult
            Container with 18 statistical measures of objective function coefficients.

        """
        (abscoefs_c, abscoefs_nc, abscoefs_v), (indices_c, indices_nc, indices_v) = self._abs_coefficients(model)

        ac = constraint_matrix(model, degree=1, vtype=Vtype.Real)
        anc = constraint_matrix(model, degree=1, vtype=[Vtype.Integer, Vtype.Binary])
        av = constraint_matrix(model, degree=1, vtype=None)

        norm_abscoefs_c = self._normalize(ac, abscoefs_c, indices_c)  # type: ignore[reportargumentType]
        norm_abscoefs_nc = self._normalize(anc, abscoefs_nc, indices_nc)  # type: ignore[reportargumentType]
        norm_abscoefs_v = self._normalize(av, abscoefs_v, indices_v)  # type: ignore[reportargumentType]

        sqrtnorm_abscoefs_c = self._normalize(ac, abscoefs_c, indices_c, np.sqrt)  # type: ignore[reportargumentType]
        sqrtnorm_abscoefs_nc = self._normalize(anc, abscoefs_nc, indices_nc, np.sqrt)  # type: ignore[reportargumentType]
        sqrtnorm_abscoefs_v = self._normalize(av, abscoefs_v, indices_v, np.sqrt)  # type: ignore[reportargumentType]

        return ObjectiveFunctionFeatureResult(
            # absolute objective function coefficients - continuous
            mean_abscoefs_c=mean(abscoefs_c),
            std_abscoefs_c=std(abscoefs_c),
            # absolute objective function coefficients - non-continuous
            mean_abscoefs_nc=mean(abscoefs_nc),
            std_abscoefs_nc=std(abscoefs_nc),
            # absolute objective function coefficients - all
            mean_abscoefs_v=mean(abscoefs_v),
            std_abscoefs_v=std(abscoefs_v),
            # Normalized absolute objective function coefficients - continuous
            mean_norm_abscoefs_c=mean(norm_abscoefs_c),
            std_norm_abscoefs_c=std(norm_abscoefs_c),
            # Normalized absolute objective function coefficients - non-continuous
            mean_norm_abscoefs_nc=mean(norm_abscoefs_nc),
            std_norm_abscoefs_nc=std(norm_abscoefs_nc),
            # Normalized absolute objective function coefficients - all
            mean_norm_abscoefs_v=mean(norm_abscoefs_v),
            std_norm_abscoefs_v=std(norm_abscoefs_v),
            # Square-root-normalized absolute objective function coefficients - continuous
            mean_sqrtnorm_abscoefs_c=mean(sqrtnorm_abscoefs_c),
            std_sqrtnorm_abscoefs_c=std(sqrtnorm_abscoefs_c),
            # Square-root-normalized absolute objective function coefficients - non-continuous
            mean_sqrtnorm_abscoefs_nc=mean(sqrtnorm_abscoefs_nc),
            std_sqrtnorm_abscoefs_nc=std(sqrtnorm_abscoefs_nc),
            # Square-root-normalized absolute objective function coefficients - all
            mean_sqrtnorm_abscoefs_v=mean(sqrtnorm_abscoefs_v),
            std_sqrtnorm_abscoefs_v=std(sqrtnorm_abscoefs_v),
        )

    def _normalize(
        self,
        a: NDArray,
        coefs: NDArray,
        var_indices: list[int],
        f: Callable[[NDArray], NDArray] = lambda x: x,
    ) -> NDArray:
        nonzeros = f(np.count_nonzero(a[:, var_indices], axis=0))

        if any(nonzeros == 0):
            return np.zeros_like(nonzeros)
        return coefs / f(nonzeros)

    def _abs_coefficients(
        self, model: Model
    ) -> tuple[tuple[NDArray, NDArray, NDArray], tuple[list[int], list[int], list[int]]]:
        d_coefs_c = {}
        d_coefs_nc = {}
        d_coefs_v = {}

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

        coefs_c = np.abs([d_coefs_c[var] for var in vars_c])
        coefs_nc = np.abs([d_coefs_nc[var] for var in vars_nc])
        coefs_v = np.abs([d_coefs_v[var] for var in vars_v])

        # Indices should be relative to their own filtered lists, not vars_v
        indices_c = list(range(len(vars_c)))
        indices_nc = list(range(len(vars_nc)))
        indices_v = list(range(len(vars_v)))

        return (coefs_c, coefs_nc, coefs_v), (indices_c, indices_nc, indices_v)
