from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from luna_quantum import Comparator
from pydantic import BaseModel

from luna_bench.base_components import BaseFeature
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model

from luna_bench.components.features.enum_feature_result import EnumFeatureResult


class ComparatorError(Exception):
    """
    Error raised during comparison operations.

    Attributes
    ----------
    message : str
        Description of the error
    """

    def __init__(self, constraint_name: str) -> None:
        message = f"No matching constraint comparator found for constraint {constraint_name}!"
        super().__init__(message)


class ConstraintSense(StrEnum):
    """Sense/type of constraint based on comparator."""

    LEQ = "leq"  # Less-than-or-equal (<=)
    EQ = "eq"  # Equality (==)
    GEQ = "geq"  # Greater-than-or-equal (>=)


class RhsStatsKey(NamedTuple):
    """
    Key for accessing RHS statistics.

    Attributes
    ----------
    constraint_sense : ConstraintSense
        The sense of the constraint (LEQ, EQ, or GEQ).
    """

    constraint_sense: ConstraintSense


class RhsStats(BaseModel):
    """
    Container for right-hand side statistics.

    Attributes
    ----------
    mean : float
        Mean of RHS values.
    std : float
        Standard deviation of RHS values.
    """

    mean: float
    std: float


class RightHandSideFeaturesResult(EnumFeatureResult[RhsStatsKey, RhsStats]):
    """
    Result container for right-hand side feature calculations.

    Example
    -------
    .. code-block:: python

        from luna_bench.components.features.mip.right_hand_side_feature import (
            ConstraintSense,
            RhsStatsKey,
            RightHandSideFeatures,
        )

        result = RightHandSideFeatures().run(model)
        rhs_stats = result.get(RhsStatsKey(constraint_sense=ConstraintSense.LEQ))
        rhs_stats.mean
        rhs_stats.std
    """


@feature
class RightHandSideFeatures(BaseFeature):
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
        # Collect RHS values by constraint sense
        rhs_values: dict[ConstraintSense, list[float]] = {
            ConstraintSense.LEQ: [],
            ConstraintSense.EQ: [],
            ConstraintSense.GEQ: [],
        }

        for c in model.constraints:
            match c.comparator:
                case Comparator.Le:
                    rhs_values[ConstraintSense.LEQ].append(c.rhs)
                case Comparator.Eq:
                    rhs_values[ConstraintSense.EQ].append(c.rhs)
                case Comparator.Ge:
                    rhs_values[ConstraintSense.GEQ].append(c.rhs)
                case _:
                    raise ComparatorError(constraint_name=c.name)

        # Build stats dict
        rhs_stats = RightHandSideFeaturesResult()
        for sense in ConstraintSense:
            rhs_array = np.array(rhs_values[sense])
            stats_key = RhsStatsKey(constraint_sense=sense)
            stats_value = RhsStats(mean=NumpyStatsHelper.mean(rhs_array), std=NumpyStatsHelper.std(rhs_array))
            rhs_stats.add(stats_key, stats_value)

        return rhs_stats
