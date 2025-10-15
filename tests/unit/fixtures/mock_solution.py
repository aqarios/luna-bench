import pytest
from luna_quantum import Solution, Vtype


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

    return Solution._build(  # type: ignore[attr-defined,no-any-return]
        component_types=[Vtype.Binary] * len(row),
        binary_cols=[[element] for element in row],
        spin_cols=None,
        int_cols=None,
        real_cols=None,
        raw_energies=None,
        timing=None,
        counts=[1],
    )
