from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Comparator

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model


class ComparatorError(Exception):
    """
    Error raised during comparison operations.

    Attributes
    ----------
    message : str
        Description of the error
    """

    def __init__(self, constraint_name: str) -> None:
        message = f"No matching constraint comporator found for constraint {constraint_name}!"
        super().__init__(message)


class RightHandSideFeaturesResult(ArbitraryDataDomain):
    """
    Result container for right-hand side feature calculations.

    This class stores statistical measures of right-hand side (RHS) values
    for different types of constraints in an optimization problem.

    Attributes
    ----------
    mean_rhs_leq_cons : float
        Mean of RHS values for less-than-or-equal constraints.
    std_rhs_leq_cons : float
        Standard deviation of RHS values for less-than-or-equal constraints.
    mean_rhs_eq_cons : float
        Mean of RHS values for equality constraints.
    std_rhs_eq_cons : float
        Standard deviation of RHS values for equality constraints.
    mean_rhs_geq_cons : float
        Mean of RHS values for greater-than-or-equal constraints.
    std_rhs_geq_cons : float
        Standard deviation of RHS values for greater-than-or-equal constraints.
    """

    # Right-hand side for leq constraints
    mean_rhs_leq_cons: float
    std_rhs_leq_cons: float

    # Right-hand side for eq constraints
    mean_rhs_eq_cons: float
    std_rhs_eq_cons: float

    # Right-hand side for geq constraints
    mean_rhs_geq_cons: float
    std_rhs_geq_cons: float


@feature
class RightHandSideFeatures(IFeature):
    """
    Feature extractor for right-hand side values of constraints.

    Extracts statistical features (mean and standard deviation) for the RHS values
    of different constraint types: less-than-or-equal (<=), equality (==), and
    greater-than-or-equal (>=) constraints.
    """

    def run(self, model: Model) -> RightHandSideFeaturesResult:
        """
        Calculate right-hand side statistical features for constraints.

        Computes mean and standard deviation of RHS values grouped by constraint
        sense (<=, ==, >=).

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        RightHandSideFeaturesResult
            Container with RHS statistical measures for each constraint type.
        """
        rhs_leq: np.typing.NDArray[np.float64] = np.array([])
        rhs_eq: np.typing.NDArray[np.float64] = np.array([])
        rhs_geq: np.typing.NDArray[np.float64] = np.array([])

        for c in model.constraints:
            if c.comparator == Comparator.Le:
                rhs_leq = np.append(rhs_leq, c.rhs)
            elif c.comparator == Comparator.Eq:
                rhs_eq = np.append(rhs_eq, c.rhs)
            elif c.comparator == Comparator.Ge:
                rhs_geq = np.append(rhs_geq, c.rhs)
            else:
                raise ComparatorError(constraint_name=c.name)

        return RightHandSideFeaturesResult(
            mean_rhs_leq_cons=NumpyStatsHelper.mean(rhs_leq),
            std_rhs_leq_cons=NumpyStatsHelper.std(rhs_leq),
            mean_rhs_eq_cons=NumpyStatsHelper.mean(rhs_eq),
            std_rhs_eq_cons=NumpyStatsHelper.std(rhs_eq),
            mean_rhs_geq_cons=NumpyStatsHelper.mean(rhs_geq),
            std_rhs_geq_cons=NumpyStatsHelper.std(rhs_geq),
        )
