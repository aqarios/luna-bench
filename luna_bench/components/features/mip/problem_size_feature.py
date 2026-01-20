from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Model, Unbounded, Vtype

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from numpy.typing import NDArray


class ModelBoundsError(Exception):
    """Raised when model bounds are None or invalid."""

    def __init__(self, model_name: str | None = None, expected_bounds: str | None = None) -> None:
        """Initialize ModdelBoundError."""
        self.model_name = model_name
        self.expected_bounds = expected_bounds
        super().__init__()

    def __str__(self) -> str:
        """Return string representation of ModelBoundError."""
        base_msg = super().__str__()
        if self.model_name:
            base_msg += f" (model: {self.model_name})"
        if self.expected_bounds:
            base_msg += f" (expected: {self.expected_bounds})"
        return base_msg


class ProblemSizeFeaturesResult(ArbitraryDataDomain):
    """
    Result container for problem size feature calculations.

    This class stores various metrics related to the size and structure of an
    optimization problem, including counts of variables and constraints by type,
    sparsity measures, and support size statistics.

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
    num_boolean_vars : int
        Number of binary/boolean variables.
    num_integer_vars : int
        Number of integer variables.
    num_cont_vars : int
        Number of continuous (real) variables.
    num_semi_cont_vars : int
        Number of semi-continuous variables.
    num_semi_integer_vars : int
        Number of semi-integer variables.
    frac_boolean_vars : float
        Fraction of boolean variables relative to total variables.
    frac_integer_vars : float
        Fraction of integer variables relative to total variables.
    frac_cont_vars : float
        Fraction of continuous variables relative to total variables.
    frac_semi_cont_vars : float
        Fraction of semi-continuous variables relative to total variables.
    frac_semi_integer_vars : float
        Fraction of semi-integer variables relative to total variables.
    num_non_cont_vars : int
        Total number of non-continuous variables (binary + integer).
    frac_non_cont_vars : float
        Fraction of non-continuous variables relative to total variables.
    num_unbounded_non_cont_vars : int
        Number of non-continuous variables without bounds.
    frac_unbounded_non_cont_vars : float
        Fraction of unbounded non-continuous variables relative to total variables.
    mean_support_size : float
        Mean support size across bounded variables.
    median_support_size : float
        Median support size across bounded variables.
    vc_support_size : float
        Variation coefficient of support sizes.
    q90_support_size : float
        90th percentile of support sizes.
    q10_support_size : float
        10th percentile of support sizes.
    """

    num_vars: int
    num_constraints: int
    num_non_zero_entries_linear_constraint_matrix: int
    num_quadratic_constraints: int
    num_non_zero_entries_quadratic_constraint_matrix: int
    num_boolean_vars: int
    num_integer_vars: int
    num_cont_vars: int
    num_semi_cont_vars: int
    num_semi_integer_vars: int
    frac_boolean_vars: float
    frac_integer_vars: float
    frac_cont_vars: float
    frac_semi_cont_vars: float
    frac_semi_integer_vars: float
    num_non_cont_vars: int
    frac_non_cont_vars: float
    num_unbounded_non_cont_vars: int
    frac_unbounded_non_cont_vars: float
    mean_support_size: float
    median_support_size: float
    vc_support_size: float
    q90_support_size: float
    q10_support_size: float


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
        num_vars = model.num_vars
        num_cons = model.num_constraints
        num_non_zero_linear = np.count_nonzero(ModelMatrix.constraint_matrix(model, ConstraintDegree.LINEAR, None)[0])
        num_non_zero_quad = np.count_nonzero(ModelMatrix.constraint_matrix(model, ConstraintDegree.QUADRATIC, None)[0])
        num_quad_constr = sum(c.lhs.degree() == ConstraintDegree.QUADRATIC for c in model.constraints)
        variables = list(model.variables())

        # luna-model does not explicity supports semi continuous / integer variables
        num_bool, num_int, num_cont, num_semi_cont, num_semi_int, num_unbound_non_cont = 0, 0, 0, 0, 0, 0
        for var in variables:
            match var.vtype:
                case Vtype.Binary:
                    num_bool += 1
                case Vtype.Integer:
                    if isinstance(var.bounds.lower, Unbounded) and isinstance(var.bounds.upper, Unbounded):
                        num_int += 1
                        num_unbound_non_cont += 1
                    elif (isinstance(var.bounds.lower, Unbounded) or isinstance(var.bounds.upper, Unbounded)) or (
                        isinstance(var.bounds.lower, float) or isinstance(var.bounds.upper, float)
                    ):
                        num_int += 1
                    else:
                        raise ModelBoundsError(model_name=model.name, expected_bounds="[-inf, inf]")
                case Vtype.Real:
                    if var.bounds.lower is None or var.bounds.upper is None:
                        raise ModelBoundsError(model_name=model.name, expected_bounds="[-inf, inf]")
                    num_cont += 1

        num_non_cont = num_bool + num_int
        support_sizes = self._support_sizes(model)

        return ProblemSizeFeaturesResult(
            num_vars=num_vars,
            num_constraints=num_cons,
            num_non_zero_entries_linear_constraint_matrix=num_non_zero_linear.astype(int),
            num_quadratic_constraints=num_quad_constr,
            num_non_zero_entries_quadratic_constraint_matrix=num_non_zero_quad.astype(int),
            num_boolean_vars=num_bool,
            num_integer_vars=num_int,
            num_cont_vars=num_cont,
            num_semi_cont_vars=num_semi_cont,
            num_semi_integer_vars=num_semi_int,
            frac_boolean_vars=num_bool / num_vars if num_vars > 0 else 0.0,
            frac_integer_vars=num_int / num_vars if num_vars > 0 else 0.0,
            frac_cont_vars=num_cont / num_vars if num_vars > 0 else 0.0,
            frac_semi_cont_vars=num_semi_cont / num_vars if num_vars > 0 else 0.0,
            frac_semi_integer_vars=num_semi_int / num_vars if num_vars > 0 else 0.0,
            num_non_cont_vars=num_non_cont,
            frac_non_cont_vars=num_non_cont / num_vars if num_vars > 0 else 0.0,
            num_unbounded_non_cont_vars=num_unbound_non_cont,
            frac_unbounded_non_cont_vars=num_unbound_non_cont / num_vars if num_vars > 0 else 0.0,
            mean_support_size=NumpyStatsHelper.mean(support_sizes),
            median_support_size=NumpyStatsHelper.median(support_sizes),
            vc_support_size=NumpyStatsHelper.vc(support_sizes),
            q90_support_size=NumpyStatsHelper.q90(support_sizes),
            q10_support_size=NumpyStatsHelper.q10(support_sizes),
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
        # errror.
        support_sizes = [
            v.bounds.upper - v.bounds.lower + 1  # type: ignore[operator]
            for v in model.variables()
            if v.vtype in [Vtype.Binary, Vtype.Integer]
            and not isinstance(v.bounds.lower, Unbounded)
            and not isinstance(v.bounds.upper, Unbounded)
        ]

        return np.array(support_sizes)
