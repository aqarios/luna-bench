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

    # continuous
    mean_abscoefs_c: float
    std_abscoefs_c: float

    # non-continuous
    mean_abscoefs_nc: float
    std_abscoefs_nc: float

    # all types
    mean_abscoefs_v: float
    std_abscoefs_v: float

    # normalized continuous
    mean_norm_abscoefs_c: float
    std_norm_abscoefs_c: float

    # normalized non-continuous
    mean_norm_abscoefs_nc: float
    std_norm_abscoefs_nc: float

    # normalized all types
    mean_norm_abscoefs_v: float
    std_norm_abscoefs_v: float

    # sqrt abs continuous
    mean_sqrtnorm_abscoefs_c: float
    std_sqrtnorm_abscoefs_c: float

    # sqrt abs non-continuous
    mean_sqrtnorm_abscoefs_nc: float
    std_sqrtnorm_abscoefs_nc: float

    # sqrt abs all types
    mean_sqrtnorm_abscoefs_v: float
    std_sqrtnorm_abscoefs_v: float


@feature
class ObjectiveFunctionFeature(IFeature):
    """Fake feature class."""

    def run(self, model: Model) -> ObjectiveFunctionFeatureResult:
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

        ac, _ = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=Vtype.Real)
        anc, _ = ModelMatrix.constraint_matrix(
            model, degree=ConstraintDegree.LINEAR, vtype=[Vtype.Integer, Vtype.Binary]
        )
        av, _ = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=None)

        norm_abscoefs_c = self._normalize(ac, abscoefs_c, indices_c)
        norm_abscoefs_nc = self._normalize(anc, abscoefs_nc, indices_nc)
        norm_abscoefs_v = self._normalize(av, abscoefs_v, indices_v)

        sqrtnorm_abscoefs_c = self._normalize(ac, abscoefs_c, indices_c, np.sqrt)
        sqrtnorm_abscoefs_nc = self._normalize(anc, abscoefs_nc, indices_nc, np.sqrt)
        sqrtnorm_abscoefs_v = self._normalize(av, abscoefs_v, indices_v, np.sqrt)

        return ObjectiveFunctionFeatureResult(
            # abs continuous
            mean_abscoefs_c=NumpyStatsHelper.mean(abscoefs_c),
            std_abscoefs_c=NumpyStatsHelper.std(abscoefs_c),
            # abs non-continuous
            mean_abscoefs_nc=NumpyStatsHelper.mean(abscoefs_nc),
            std_abscoefs_nc=NumpyStatsHelper.std(abscoefs_nc),
            # abs all types
            mean_abscoefs_v=NumpyStatsHelper.mean(abscoefs_v),
            std_abscoefs_v=NumpyStatsHelper.std(abscoefs_v),
            # norm abs continuous
            mean_norm_abscoefs_c=NumpyStatsHelper.mean(norm_abscoefs_c),
            std_norm_abscoefs_c=NumpyStatsHelper.std(norm_abscoefs_c),
            # norm abs non-continuous
            mean_norm_abscoefs_nc=NumpyStatsHelper.mean(norm_abscoefs_nc),
            std_norm_abscoefs_nc=NumpyStatsHelper.std(norm_abscoefs_nc),
            # norm abs all
            mean_norm_abscoefs_v=NumpyStatsHelper.mean(norm_abscoefs_v),
            std_norm_abscoefs_v=NumpyStatsHelper.std(norm_abscoefs_v),
            # sqrt norm abs continuous
            mean_sqrtnorm_abscoefs_c=NumpyStatsHelper.mean(sqrtnorm_abscoefs_c),
            std_sqrtnorm_abscoefs_c=NumpyStatsHelper.std(sqrtnorm_abscoefs_c),
            # sqrt norm abs non-continuous
            mean_sqrtnorm_abscoefs_nc=NumpyStatsHelper.mean(sqrtnorm_abscoefs_nc),
            std_sqrtnorm_abscoefs_nc=NumpyStatsHelper.std(sqrtnorm_abscoefs_nc),
            # sqrt norm abs all types
            mean_sqrtnorm_abscoefs_v=NumpyStatsHelper.mean(sqrtnorm_abscoefs_v),
            std_sqrtnorm_abscoefs_v=NumpyStatsHelper.std(sqrtnorm_abscoefs_v),
        )

    def _normalize(
        self,
        a: NDArray[np.float64],
        coefs: NDArray[np.float64],
        var_indices: list[int],
        f: Callable[[NDArray[np.float64]], NDArray[np.float64]] = lambda x: x,
    ) -> NDArray[np.float64]:
        nonzeros = f(np.count_nonzero(a[:, var_indices], axis=0))

        if any(nonzeros == 0):
            return np.zeros_like(nonzeros, dtype=np.float64)
        return coefs / f(nonzeros)

    def _abs_coefficients(
        self, model: Model
    ) -> tuple[
        tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]], tuple[list[int], list[int], list[int]]
    ]:
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
