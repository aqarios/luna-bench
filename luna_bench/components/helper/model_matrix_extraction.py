from typing import Literal, overload

import numpy as np
from luna_quantum import Constraint, Model, Variable, Vtype
from numpy.typing import NDArray

from luna_bench.components.helper.degree import ConstraintDegree


class ModelMatrix:
    """Helper class for extracting constraint and objective matrices from a Model."""

    @staticmethod
    @overload
    def constraint_matrix(
        model: Model, degree: int, vtype: Vtype | list[Vtype] | None, *, include_b: Literal[True]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]: ...

    @staticmethod
    @overload
    def constraint_matrix(
        model: Model, degree: int, vtype: Vtype | list[Vtype] | None, *, include_b: Literal[False] = False
    ) -> tuple[NDArray[np.float64], None]: ...

    @staticmethod
    def constraint_matrix(
        model: Model,
        degree: int,
        vtype: list[Vtype] | Vtype | None,
        *,
        include_b: bool = False,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]] | tuple[NDArray[np.float64], None]:
        """
        Extract constraint matrix from a Model, optionally filtering by variable type and constraint degree.

        For degree=1: Returns standard constraint matrix where a[i,j] is the coefficient of variable j
        in constraint i.
        For degree=2: Returns a flattened representation where quadratic terms x_i*x_j are mapped to
        columns. The column ordering is: [linear terms | quadratic terms (i,j) where i <= j]

        Parameters
        ----------
        model : Model
            The optimization model to extract constraints from.
        degree : int
            The degree of constraints to extract (1 for linear, 2 for quadratic).
        vtype : list[Vtype] | Vtype | None
            Variable type filter.
        include_b : bool, optional
            If True, return both constraint matrix (a) and RHS vector (b).

        Returns
        -------
        tuple[NDArray[np.float64], NDArray[np.float64]] | tuple[NDArray[np.float64], None]
            Constraint matrix a and RHS vector b (or None if ``include_b`` is False).
        """
        # Filter variables by type
        variables: list[Variable]
        if vtype is None:
            variables = list(model.variables())
        elif isinstance(vtype, list):
            variables = [v for v in model.variables() if v.vtype in vtype]
        else:
            variables = [v for v in model.variables() if v.vtype == vtype]

        constraints = [c for c in model.constraints if c.lhs.degree() == degree]
        variable_order = {var: idx for idx, var in enumerate(variables)}

        if degree == ConstraintDegree.LINEAR:
            a, b = ModelMatrix._extract_linear_degree(constraints, variables, variable_order)

        elif degree == ConstraintDegree.QUADRATIC:
            a, b = ModelMatrix._extract_quad_degree(constraints, variables, variable_order)
        else:
            raise NotImplementedError(f"Degree {degree} constraints are not yet supported")

        if include_b:
            return (a, b)
        return (a, None)

    @staticmethod
    def _extract_linear_degree(
        constraints: list[Constraint], variables: list[Variable], variable_order: dict[Variable, int]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        # Standard linear constraint matrix
        a = np.zeros((len(constraints), len(variables)))
        b = np.zeros(len(constraints))

        for i, c in enumerate(constraints):
            for var, coef in c.lhs.linear_items():
                if var in variable_order:
                    a[i, variable_order[var]] = coef
            b[i] = c.rhs

        return a, b

    @staticmethod
    def _extract_quad_degree(
        constraints: list[Constraint], variables: list[Variable], variable_order: dict[Variable, int]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        # For quadratic constraints, we need to handle both linear and quadratic terms
        # Column structure: [linear terms | quadratic terms]

        # Determine quadratic variable pairs across all constraints
        quad_pairs = set()
        for c in constraints:
            for var1, var2, _ in c.lhs.quadratic_items():
                if var1 in variable_order and var2 in variable_order:
                    i, j = sorted([variable_order[var1], variable_order[var2]])
                    pair = (min(i, j), max(i, j))
                    quad_pairs.add(pair)

        quad_pairs_list = sorted(quad_pairs)
        quad_pair_to_col = {pair: idx + len(variables) for idx, pair in enumerate(quad_pairs_list)}

        n_cols = len(variables) + len(quad_pairs_list)
        a = np.zeros((len(constraints), n_cols))
        b = np.zeros(len(constraints))

        for i, c in enumerate(constraints):
            for var, coef in c.lhs.linear_items():
                if var in variable_order:
                    a[i, variable_order[var]] = coef

            for var1, var2, coef in c.lhs.quadratic_items():
                if var1 in variable_order and var2 in variable_order:
                    idx1, idx2 = variable_order[var1], variable_order[var2]
                    pair = (min(idx1, idx2), max(idx1, idx2))
                    col = quad_pair_to_col[pair]
                    a[i, col] = coef

            b[i] = c.rhs

        return a, b
