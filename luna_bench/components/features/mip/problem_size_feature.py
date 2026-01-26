from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from luna_quantum import Model, Unbounded, Vtype
from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.components.features.base_feature import BaseFeatureResult
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from numpy.typing import NDArray


class ModelBoundsError(Exception):
    """Raised when model bounds are None or invalid."""

    def __init__(self, model_name: str | None = None, expected_bounds: str | None = None) -> None:
        """Initialize ModelBoundsError."""
        self.model_name = model_name
        self.expected_bounds = expected_bounds
        super().__init__()

    def __str__(self) -> str:
        """Return string representation of ModelBoundsError."""
        base_msg = super().__str__()
        if self.model_name:
            base_msg += f" (model: {self.model_name})"
        if self.expected_bounds:
            base_msg += f" (expected: {self.expected_bounds})"
        return base_msg


class VarType(str, Enum):
    """Type of variable being counted."""

    BOOLEAN = "boolean"  # Binary variables
    INTEGER = "integer"  # Integer variables
    CONTINUOUS = "continuous"  # Real/continuous variables
    SEMI_CONTINUOUS = "semi_continuous"  # Semi-continuous variables
    SEMI_INTEGER = "semi_integer"  # Semi-integer variables
    NON_CONTINUOUS = "non_continuous"  # Binary + Integer combined
    UNBOUNDED_NON_CONTINUOUS = "unbounded_non_continuous"  # Non-continuous without bounds


class VarTypeKey(NamedTuple):
    """Key for accessing variable count statistics."""

    var_type: VarType


class VarCountStats(BaseModel):
    """
    Container for variable count statistics.

    Attributes
    ----------
    count : int
        Absolute count of variables of this type.
    fraction : float
        Fraction of total variables (count / num_vars).
    """

    count: int
    fraction: float


class VarCountResult(BaseFeatureResult[VarTypeKey, VarCountStats]):
    """
    Result container for variable count statistics.

    Access via VarTypeKey:
        result.stats[VarTypeKey(var_type=VarType.BOOLEAN).key]
    """


class SupportSizeStats(BaseModel):
    """
    Container for support size statistics.

    Attributes
    ----------
    mean : float
        Mean support size across bounded variables.
    median : float
        Median support size across bounded variables.
    variation_coefficient : float
        Variation coefficient of support sizes.
    q90 : float
        90th percentile of support sizes.
    q10 : float
        10th percentile of support sizes.
    """

    mean: float
    median: float
    variation_coefficient: float
    q90: float
    q10: float


class ProblemSizeFeaturesResult(ArbitraryDataDomain):
    """
    Result container for problem size feature calculations.

    This class stores various metrics related to the size and structure of an
    optimization problem, including counts of variables and constraints by type,
    sparsity measures, and support size statistics.

    Access patterns for variable counts:
        - result.var_counts.get(VarType.BOOLEAN) -> VarCountStats
        - result.var_counts.get_num(VarType.BOOLEAN) -> int
        - result.var_counts.get_frac(VarType.BOOLEAN) -> float

    Attributes
    ----------
    num_vars : int
        Total number of variables in the model.
    num_constraints : int
        Total number of constraints in the model.
    num_non_zero_entries_linear_constraint_matrix : int
        Number of non-zero entries in the linear constraint matrix.
    num_quadratic_constraints : int
        Number of quadratic constraints.
    num_non_zero_entries_quadratic_constraint_matrix : int
        Number of non-zero entries in the quadratic constraint matrix.
    var_counts : VarCountResult
        Variable count statistics organized by type.
    support_size : SupportSizeStats
        Statistical measures of variable support sizes.
    """

    num_vars: int
    num_constraints: int
    num_non_zero_entries_linear_constraint_matrix: int
    num_quadratic_constraints: int
    num_non_zero_entries_quadratic_constraint_matrix: int
    var_counts: VarCountResult
    support_size: SupportSizeStats


@feature
class ProblemSizeFeatures(IFeature):
    """
    Feature extractor for problem size-related characteristics.

    Extracts features related to the number and types of variables, constraints,
    and the sparsity of constraint matrices. Includes both absolute counts and
    fractional values, as well as statistical metrics related to variable support sizes.
    """

    def run(self, model: Model) -> ProblemSizeFeaturesResult:
        """
        Calculate problem size features for the given optimization model.

        Computes various metrics including variable counts by type, constraint counts,
        matrix sparsity measures, and support size statistics for bounded variables.

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        ProblemSizeFeaturesResult
            Container with problem size metrics.
        """
        num_vars = model.num_variables
        num_cons = model.num_constraints
        num_non_zero_linear = np.count_nonzero(ModelMatrix.constraint_matrix(model, ConstraintDegree.LINEAR, None)[0])
        num_non_zero_quad = np.count_nonzero(ModelMatrix.constraint_matrix(model, ConstraintDegree.QUADRATIC, None)[0])
        num_quad_constr = sum(c.lhs.degree() == ConstraintDegree.QUADRATIC for c in model.constraints)
        variables = list(model.variables())

        # Count variables by type
        counts = {
            VarType.BOOLEAN: 0,
            VarType.INTEGER: 0,
            VarType.CONTINUOUS: 0,
            VarType.SEMI_CONTINUOUS: 0,
            VarType.SEMI_INTEGER: 0,
            VarType.UNBOUNDED_NON_CONTINUOUS: 0,
        }

        for var in variables:
            match var.vtype:
                case Vtype.Binary:
                    counts[VarType.BOOLEAN] += 1
                case Vtype.Integer:
                    if isinstance(var.bounds.lower, Unbounded) and isinstance(var.bounds.upper, Unbounded):
                        counts[VarType.INTEGER] += 1
                        counts[VarType.UNBOUNDED_NON_CONTINUOUS] += 1
                    elif (isinstance(var.bounds.lower, Unbounded) or isinstance(var.bounds.upper, Unbounded)) or (
                        isinstance(var.bounds.lower, float) or isinstance(var.bounds.upper, float)
                    ):
                        counts[VarType.INTEGER] += 1
                    else:
                        raise ModelBoundsError(model_name=model.name, expected_bounds="[-inf, inf]")
                case Vtype.Real:
                    if var.bounds.lower is None or var.bounds.upper is None:
                        raise ModelBoundsError(model_name=model.name, expected_bounds="[-inf, inf]")
                    counts[VarType.CONTINUOUS] += 1

        # Compute derived count
        counts[VarType.NON_CONTINUOUS] = counts[VarType.BOOLEAN] + counts[VarType.INTEGER]

        # Build var_counts dict with VarCountStats
        var_counts_dict: dict[str, VarCountStats] = {}
        for var_type, count in counts.items():
            key = VarTypeKey(var_type=var_type)
            var_counts_dict[str(key._asdict())] = VarCountStats(
                count=count,
                fraction=count / num_vars if num_vars > 0 else 0.0,
            )

        var_counts = VarCountResult(stats=var_counts_dict)

        # Calculate support size statistics
        support_sizes = self._support_sizes(model)
        support_size_stats = SupportSizeStats(
            mean=NumpyStatsHelper.mean(support_sizes),
            median=NumpyStatsHelper.median(support_sizes),
            variation_coefficient=NumpyStatsHelper.vc(support_sizes),
            q90=NumpyStatsHelper.q90(support_sizes),
            q10=NumpyStatsHelper.q10(support_sizes),
        )

        return ProblemSizeFeaturesResult(
            num_vars=num_vars,
            num_constraints=num_cons,
            num_non_zero_entries_linear_constraint_matrix=int(num_non_zero_linear),
            num_quadratic_constraints=num_quad_constr,
            num_non_zero_entries_quadratic_constraint_matrix=int(num_non_zero_quad),
            var_counts=var_counts,
            support_size=support_size_stats,
        )

    def _support_sizes(self, model: Model) -> NDArray[np.float64]:
        """
        Calculate support sizes for bounded variables.

        Computes domain size for binary/integer variables. For semi-continuous
        variables this would be 2, and for semi-integer variables this would be
        1 + domain size (not currently implemented).

        Parameters
        ----------
        model : Model
            The optimization model.

        Returns
        -------
        NDArray
            Array of support sizes for bounded variables.
        """
        # Because luna model defines upper / lowerbound as unbounded and none, typing gives an irrelevant
        # error.
        support_sizes = [
            v.bounds.upper - v.bounds.lower + 1  # type: ignore[operator]
            for v in model.variables()
            if v.vtype in [Vtype.Binary, Vtype.Integer]
            and not isinstance(v.bounds.lower, Unbounded)
            and not isinstance(v.bounds.upper, Unbounded)
        ]

        return np.array(support_sizes)
