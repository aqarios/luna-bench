import pytest
from luna_model import Solution, Vtype


@pytest.fixture()
def solution() -> Solution:
    row = [
        0,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        0,
    ]

    return Solution(
        [{f"x{i}": v for i, v in enumerate(row)}],
        vtypes=[Vtype.BINARY] * len(row),
        raw_energies=None,
        timing=None,
        counts=[1],
    )
