import numpy as np


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
        msg = "Approximation Ratio is not implemented for cases dividing by 0!"
        raise ZeroDivisionError(msg)
    return nominator / denominator
