from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Comparator

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature

from .utils import mean, std

if TYPE_CHECKING:
    from luna_quantum import Model


class RightHandSideFeaturesResult(ArbitraryDataDomain):
    """
    Result container for right-hand side feature calculations.

    This class stores statistical measures of right-hand side (RHS) values
    for different types of constraints in an optimization problem.

    Attributes
    ----------
    mean_right_hand_side_leq_constraints : float
        Mean of RHS values for less-than-or-equal constraints.
    std_right_hand_side_leq_constraints : float
        Standard deviation of RHS values for less-than-or-equal constraints.
    mean_right_hand_side_eq_constraints : float
        Mean of RHS values for equality constraints.
    std_right_hand_side_eq_constraints : float
        Standard deviation of RHS values for equality constraints.
    mean_right_hand_side_geq_constraints : float
        Mean of RHS values for greater-than-or-equal constraints.
    std_right_hand_side_geq_constraints : float
        Standard deviation of RHS values for greater-than-or-equal constraints.
    """

    # Right-hand side for leq constraints
    mean_right_hand_side_leq_constraints: float
    std_right_hand_side_leq_constraints: float

    # Right-hand side for eq constraints
    mean_right_hand_side_eq_constraints: float
    std_right_hand_side_eq_constraints: float

    # Right-hand side for geq constraints
    mean_right_hand_side_geq_constraints: float
    std_right_hand_side_geq_constraints: float


@feature
class RightHandSideFeatures(IFeature):
    """
    Feature extractor for right-hand side values of constraints.

    Extracts statistical features (mean and standard deviation) for the RHS values
    of different constraint types: less-than-or-equal (<=), equality (==), and
    greater-than-or-equal (>=) constraints.
    """

    def run(self, model: Model) -> ArbitraryDataDomain:
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
        rhs_leq, rhs_eq, rhs_geq = [], [], []

        for c in model.constraints:
            match type(c.comparator):
                case Comparator.Le:
                    rhs_leq.append(c.rhs)
                case Comparator.Eq:
                    rhs_eq.append(c.rhs)
                case Comparator.Ge:
                    rhs_geq.append(c.rhs)

        rhs_leq = np.array(rhs_leq)
        rhs_eq = np.array(rhs_eq)
        rhs_geq = np.array(rhs_geq)

        return RightHandSideFeaturesResult(
            mean_right_hand_side_leq_constraints=mean(rhs_leq),
            std_right_hand_side_leq_constraints=std(rhs_leq),
            mean_right_hand_side_eq_constraints=mean(rhs_eq),
            std_right_hand_side_eq_constraints=std(rhs_eq),
            mean_right_hand_side_geq_constraints=mean(rhs_geq),
            std_right_hand_side_geq_constraints=std(rhs_geq),
        )
