from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Comparator
from pydantic import BaseModel

from luna_bench._internal.interfaces import IFeature
from luna_bench.components.features.base_results import BaseStatsResult1D
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
        message = f"No matching constraint comparator found for constraint {constraint_name}!"
        super().__init__(message)


class ConstraintSense(str, Enum):
    """Sense/type of constraint based on comparator."""

    LEQ = "leq"  # Less-than-or-equal (<=)
    EQ = "eq"  # Equality (==)
    GEQ = "geq"  # Greater-than-or-equal (>=)


class RhsStats(BaseModel):
    """
    Container for right-hand side statistics with descriptive context.

    Attributes
    ----------
    constraint_sense : ConstraintSense
        The sense of the constraint (leq, eq, geq).
    mean : float
        Mean of RHS values.
    std : float
        Standard deviation of RHS values.
    """

    constraint_sense: ConstraintSense
    mean: float
    std: float


class RightHandSideFeaturesResult(BaseStatsResult1D[ConstraintSense, RhsStats]):
    """
    Result container for right-hand side feature calculations.

    This class stores statistical measures of right-hand side (RHS) values
    for different types of constraints in an optimization problem.

    Access patterns:
        - result.get(ConstraintSense.LEQ) -> RhsStats
        - result.get_mean(ConstraintSense.LEQ) -> float
        - result.get_std(ConstraintSense.LEQ) -> float
        - result.all_stats() -> Dict[ConstraintSense, RhsStats]

    Attributes
    ----------
    stats : Dict[str, RhsStats]
        Dictionary mapping constraint_sense keys to RhsStats objects.
    """

    @staticmethod
    def _type_enum() -> type[ConstraintSense]:
        """Return the ConstraintSense enum class."""
        return ConstraintSense

    def get_std(self, constraint_sense: ConstraintSense) -> float:
        """Direct access to standard deviation."""
        return self.get(constraint_sense).std


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
        # Map Comparator to ConstraintSense
        comparator_to_sense = {
            Comparator.Le: ConstraintSense.LEQ,
            Comparator.Eq: ConstraintSense.EQ,
            Comparator.Ge: ConstraintSense.GEQ,
        }

        # Collect RHS values by constraint sense
        rhs_values: dict[ConstraintSense, list[float]] = {
            ConstraintSense.LEQ: [],
            ConstraintSense.EQ: [],
            ConstraintSense.GEQ: [],
        }

        for c in model.constraints:
            sense = comparator_to_sense.get(c.comparator)
            if sense is None:
                raise ComparatorError(constraint_name=c.name)
            rhs_values[sense].append(c.rhs)

        # Build stats dict
        stats: dict[str, RhsStats] = {}
        for sense in ConstraintSense:
            rhs_array = np.array(rhs_values[sense])
            stats[RightHandSideFeaturesResult.make_key(sense)] = RhsStats(
                constraint_sense=sense,
                mean=NumpyStatsHelper.mean(rhs_array),
                std=NumpyStatsHelper.std(rhs_array),
            )

        return RightHandSideFeaturesResult(stats=stats)
