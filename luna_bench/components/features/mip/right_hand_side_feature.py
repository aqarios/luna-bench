from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from luna_quantum import Comparator
from pydantic import BaseModel

from luna_bench._internal.interfaces import IFeature
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model

from luna_bench.components.features.base_feature import BaseFeatureResult


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


class ConstraintSense(str, Enum):
    """Sense/type of constraint based on comparator."""

    LEQ = "leq"  # Less-than-or-equal (<=)
    EQ = "eq"  # Equality (==)
    GEQ = "geq"  # Greater-than-or-equal (>=)


class RhsStatsKey(NamedTuple):
    """Key for accessing RHS statistics."""

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


class RightHandSideFeaturesResult(BaseFeatureResult[RhsStatsKey, RhsStats]):
    """
    Result container for right-hand side feature calculations.

    Access via RhsStatsKey:
        result.stats[RhsStatsKey(constraint_sense=ConstraintSense.LEQ).key]
    """


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
        stats: dict[str, RhsStats] = {}
        for sense in ConstraintSense:
            rhs_array = np.array(rhs_values[sense])
            stats[str(RhsStatsKey(constraint_sense=sense)._asdict())] = RhsStats(
                mean=NumpyStatsHelper.mean(rhs_array),
                std=NumpyStatsHelper.std(rhs_array),
            )

        return RightHandSideFeaturesResult(stats=stats)
