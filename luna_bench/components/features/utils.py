import numpy as np
from luna_quantum import Model, Variable, Vtype
from numpy.typing import NDarray

LINEAR_DEGREE = 1
QUADRATIC_DEGREE = 2

def mean(data: np.ndarray) -> float:
    """Calculate the mean of the array, returning 0 if empty."""
    return data.mean() if len(data) != 0 else 0


def std(data: np.ndarray) -> float:
    """Calculate the standard deviation of the array, returning 0 if empty."""
    return data.std() if len(data) != 0 else 0


def var(data: np.ndarray) -> float:
    """Calculate the variance of the array, returning 0 if empty."""
    return data.var() if len(data) != 0 else 0


def normalized(data: np.ndarray) -> np.ndarray:
    """Normalize the array by dividing by its sum."""
    return data / np.sum(data) if np.sum(data) != 0 else data


def sqrt_normalized(data: np.ndarray) -> np.ndarray:
    """Normalize the array and then apply square root."""
    data = data / np.sum(data) if np.sum(data) != 0 else data
    return np.sqrt(data)


def median(data: np.ndarray) -> float:
    """Calculate the median of the array, returning 0 if empty."""
    return np.median(data).item() if len(data) != 0 else 0


def vc(data: np.ndarray) -> float:
    """Calculate the coefficient of variation (std/mean), returning 0 if empty or mean is 0."""
    if len(data) == 0:
        return 0

    std = data.std()
    mean = data.mean()

    if mean == 0:
        return 0

    return std / mean


def q10(data: np.ndarray) -> float:
    """Calculate the 10th percentile, returning 0 if empty."""
    if len(data) == 0:
        return 0
    return np.percentile(data, 10).item()


def q90(data: np.ndarray) -> float:
    """Calculate the 90th percentile, returning 0 if empty."""
    if len(data) == 0:
        return 0
    return np.percentile(data, 90).item()


def constraint_matrix(
    model: Model,
    degree: int,
    vtype: list[Vtype] | Vtype | None,
    include_b: bool = False,
) -> NDarray | tuple[NDarray, NDarray]:
    """
    Extract constraint matrix from a Model, optionally filtering by variable type and constraint degree.

    For degree=1: Returns standard constraint matrix where a[i,j] is the coefficient of variable j in constraint i.
    For degree=2: Returns a flattened representation where quadratic terms x_i*x_j are mapped to columns.
                  The column ordering is: [linear terms | quadratic terms (i,j) where i <= j]

    args:
        model (Model): The optimization model to extract constraints from.
        degree (int): The degree of constraints to extract (1 for linear, 2 for quadratic).
        vtype (list[Vtype] | Vtype | None): Variable type filter.
        include_b (bool, optional): If True, return both constraint matrix (a) and RHS vector (b).

    Returns
    -------
        NDarray | tuple[NDarray, NDarray]: Constraint matrix a (and optionally RHS vector b)
    """
    # Filter variables by type
    variables: list[Variable]
    if vtype is None:
        variables = list(model.variables())
    elif isinstance(vtype, list):
        variables = [v for v in model.variables() if v.vtype in vtype]
    else:
        variables = [v for v in model.variables() if v.vtype == vtype]

    # Get constraints of the specified degree
    constraints = [c for c in model.constraints if c.lhs.degree() == degree]
    variable_order = {var: idx for idx, var in enumerate(variables)}

    if degree == LINEAR_DEGREE:
        # Standard linear constraint matrix
        a = np.zeros((len(constraints), len(variables)))
        b = np.zeros(len(constraints))

        for i, c in enumerate(constraints):
            for var, coef in c.lhs.linear_items():
                if var in variable_order:
                    a[i, variable_order[var]] = coef
            b[i] = c.rhs

    elif degree == QUADRATIC_DEGREE:
        # For quadratic constraints, we need to handle both linear and quadratic terms
        # Column structure: [linear terms | quadratic terms]

        # First, collect all unique quadratic variable pairs across all constraints
        quad_pairs = set()
        for c in constraints:
            for var1, var2, _ in c.lhs.quadratic_items():
                if var1 in variable_order and var2 in variable_order:
                    # Ensure consistent ordering (i <= j)
                    i, j = sorted([variable_order[var1], variable_order[var2]])
                    quad_pairs.add((i, j))

        # Create ordered list of quadratic pairs
        quad_pairs_list = sorted(quad_pairs)
        quad_pair_to_col = {pair: idx + len(variables) for idx, pair in enumerate(quad_pairs_list)}

        # Total columns: linear terms + quadratic terms
        n_cols = len(variables) + len(quad_pairs_list)
        a = np.zeros((len(constraints), n_cols))
        b = np.zeros(len(constraints))

        for i, c in enumerate(constraints):
            # Handle linear terms
            for var, coef in c.lhs.linear_items():
                if var in variable_order:
                    a[i, variable_order[var]] = coef

            # Handle quadratic terms
            for var1, var2, coef in c.lhs.quadratic_items():
                if var1 in variable_order and var2 in variable_order:
                    idx1, idx2 = variable_order[var1], variable_order[var2]
                    pair = tuple(sorted([idx1, idx2]))
                    col = quad_pair_to_col[pair]
                    a[i, col] = coef

            b[i] = c.rhs
    else:
        raise NotImplementedError(f"Degree {degree} constraints are not yet supported")

    return (a, b) if include_b else a
