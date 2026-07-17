import numpy as np
from annotated_types import Ge, Le
from pydantic.fields import FieldInfo


def get_ratio(nominator: float, denominator: float, abt_diff: float) -> float:
    """Calculate the ratio of two values with zero-division protection.

    Parameters
    ----------
    nominator : float
        The numerator of the ratio.
    denominator : float
        The denominator of the ratio.
    abt_diff : float
        The absolute tolerance for zero-division.

    Returns
    -------
    float
        The calculated ratio (nominator / denominator).

    Raises
    ------
    ZeroDivisionError
        Raised if the denominator is close to zero (within abt_diff tolerance).
    """
    if np.isclose(denominator, 0, atol=abt_diff):
        msg = "Ratio is not defined for cases where denominator is 0!"
        raise ZeroDivisionError(msg)
    return nominator / denominator


def snap_to_bounds(value: float, field_info: FieldInfo, abs_tol: float) -> float:
    """Snap a value to the field's `ge`/`le` bounds if it is within tolerance.

    Parameters
    ----------
    value : float
        The value to snap.
    field_info : FieldInfo
        The pydantic field whose `ge`/`le` constraints define the bounds.
    abs_tol : float
        The absolute tolerance within which the value is snapped to a bound.

    Returns
    -------
    float
        The bound if the value is within tolerance of it, otherwise the value.
    """
    lb = next((meta.ge for meta in field_info.metadata if isinstance(meta, Ge)), None)
    ub = next((meta.le for meta in field_info.metadata if isinstance(meta, Le)), None)

    if isinstance(ub, (int, float)) and np.isclose(value, ub, atol=abs_tol):
        return float(ub)
    if isinstance(lb, (int, float)) and np.isclose(value, lb, atol=abs_tol):
        return float(lb)
    return value
