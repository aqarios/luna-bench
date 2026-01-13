from enum import IntEnum


class ConstraintDegree(IntEnum):
    """Enum representing the polynomial degree of expressions, either objective or constraints."""

    LINEAR = 1
    QUADRATIC = 2
