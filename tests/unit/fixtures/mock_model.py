import numpy as np
import pytest
from _pytest.fixtures import FixtureRequest
from luna_quantum import Model, Variable, Vtype, quicksum

from tests.utils.luna_model import simple_model


@pytest.fixture()
def model(request: FixtureRequest) -> Model:
    name: str = getattr(request, "param", "default_model")

    return simple_model(name)


@pytest.fixture()
def hard_model() -> Model:
    """
    Create a complex model that takes time to solve.

    This creates a very large multidimensional knapsack problem.
    """
    # Create the model
    model = Model(name="hard_model")

    # Constraint coefficients for x15-x74 (60 binary variables)
    c1_coefs = np.array(
        [
            74,
            49,
            12,
            93,
            56,
            16,
            39,
            77,
            56,
            73,
            1,
            3,
            68,
            61,
            8,
            55,
            18,
            21,
            57,
            98,
            58,
            57,
            46,
            72,
            6,
            16,
            76,
            21,
            78,
            18,
            11,
            58,
            59,
            25,
            32,
            14,
            16,
            3,
            60,
            12,
            7,
            42,
            98,
            34,
            33,
            16,
            97,
            63,
            66,
            28,
            57,
            19,
            74,
            44,
            45,
            49,
            76,
            74,
            9,
            44,
        ]
    )

    c2_coefs = np.array(
        [
            20,
            7,
            68,
            69,
            95,
            64,
            76,
            12,
            45,
            43,
            83,
            15,
            90,
            10,
            96,
            98,
            53,
            1,
            2,
            58,
            24,
            90,
            29,
            57,
            19,
            73,
            89,
            31,
            12,
            34,
            67,
            48,
            11,
            22,
            36,
            78,
            75,
            52,
            95,
            57,
            62,
            94,
            10,
            42,
            89,
            11,
            77,
            85,
            30,
            82,
            20,
            52,
            78,
            6,
            57,
            65,
            79,
            83,
            16,
            67,
        ]
    )

    c3_coefs = np.array(
        [
            85,
            47,
            67,
            59,
            84,
            59,
            19,
            8,
            50,
            66,
            5,
            51,
            51,
            64,
            64,
            53,
            61,
            45,
            3,
            76,
            17,
            54,
            13,
            89,
            68,
            57,
            4,
            24,
            96,
            81,
            36,
            54,
            3,
            82,
            33,
            88,
            1,
            29,
            4,
            48,
            51,
            14,
            86,
            64,
            73,
            78,
            45,
            65,
            30,
            52,
            6,
            78,
            9,
            19,
            87,
            73,
            10,
            87,
            33,
            1,
        ]
    )

    c4_coefs = np.array(
        [
            13,
            71,
            78,
            84,
            56,
            66,
            8,
            68,
            48,
            28,
            33,
            34,
            8,
            99,
            80,
            74,
            2,
            10,
            96,
            41,
            98,
            74,
            39,
            91,
            85,
            95,
            96,
            1,
            80,
            90,
            97,
            36,
            7,
            69,
            9,
            9,
            93,
            94,
            44,
            36,
            71,
            37,
            72,
            38,
            74,
            89,
            37,
            24,
            88,
            77,
            61,
            80,
            2,
            60,
            87,
            80,
            74,
            42,
            2,
            37,
        ]
    )

    c5_coefs = np.array(
        [
            35,
            61,
            66,
            78,
            46,
            89,
            61,
            25,
            55,
            16,
            81,
            35,
            96,
            23,
            83,
            39,
            14,
            53,
            23,
            23,
            93,
            38,
            15,
            20,
            19,
            28,
            79,
            51,
            24,
            6,
            3,
            47,
            61,
            60,
            71,
            63,
            26,
            66,
            71,
            63,
            56,
            32,
            39,
            31,
            64,
            89,
            62,
            68,
            59,
            71,
            48,
            76,
            96,
            74,
            61,
            21,
            46,
            18,
            23,
            24,
        ]
    )

    c6_coefs = np.array(
        [
            86,
            8,
            44,
            96,
            64,
            65,
            68,
            53,
            19,
            33,
            28,
            42,
            72,
            39,
            5,
            77,
            37,
            89,
            7,
            78,
            10,
            78,
            10,
            96,
            55,
            1,
            64,
            61,
            63,
            90,
            22,
            78,
            92,
            25,
            24,
            65,
            6,
            68,
            66,
            66,
            1,
            67,
            78,
            21,
            47,
            17,
            89,
            77,
            88,
            54,
            10,
            87,
            88,
            80,
            76,
            9,
            83,
            95,
            86,
            24,
        ]
    )

    c7_coefs = np.array(
        [
            41,
            64,
            82,
            24,
            48,
            41,
            29,
            93,
            64,
            39,
            92,
            86,
            64,
            45,
            87,
            34,
            39,
            88,
            99,
            63,
            85,
            48,
            83,
            88,
            85,
            5,
            14,
            31,
            12,
            93,
            55,
            1,
            2,
            22,
            93,
            49,
            35,
            25,
            39,
            1,
            77,
            43,
            7,
            42,
            36,
            63,
            5,
            8,
            43,
            18,
            60,
            47,
            47,
            46,
            45,
            38,
            9,
            37,
            8,
            82,
        ]
    )

    # Build constraint matrix (7 constraints x 74 variables)
    a = np.zeros((7, 74))

    # c1: x1 + x2 + ... = 1324 # noqa: ERA001
    a[0, 0:2] = [1, 1]
    a[0, 14:] = c1_coefs

    # c2: x3 + x4 + ... = 1554 # noqa: ERA001
    a[1, 2:4] = [1, 1]
    a[1, 14:] = c2_coefs

    # c3: x5 + x6 + ... = 1429 # noqa: ERA001
    a[2, 4:6] = [1, 1]
    a[2, 14:] = c3_coefs

    # c4: x7 + x8 + ... = 1686 # noqa: ERA001
    a[3, 6:8] = [1, 1]
    a[3, 14:] = c4_coefs

    # c5: x9 + x10 + ... = 1482 # noqa: ERA001
    a[4, 8:10] = [1, 1]
    a[4, 14:] = c5_coefs

    # c6: x11 + x12 + ... = 1613 # noqa: ERA001
    a[5, 10:12] = [1, 1]
    a[5, 14:] = c6_coefs

    # c7: x13 + x14 + ... = 1424 # noqa: ERA001
    a[6, 12:14] = [1, 1]
    a[6, 14:] = c7_coefs

    # Right-hand sides
    b = np.array([1324, 1554, 1429, 1686, 1482, 1613, 1424])

    # Create variables within model environment
    with model.environment:
        # Create 14 continuous slack variables (x1-x14)
        slack_vars = [model.add_variable(f"real_{i}", vtype=Vtype.Real, lower=0, upper=1) for i in range(14)]

        # Create 60 binary variables (x15-x74)
        binary_vars = [model.add_variable(f"binary_{i}", vtype=Vtype.Binary) for i in range(60)]

        # Combine all variables
        all_vars = slack_vars + binary_vars

    # Add constraints using for loop
    n, m = a.shape
    for i in range(n):
        model.add_constraint(quicksum(a[i, j] * all_vars[j] for j in range(m)) == b[i])

    # The objective function coefficients
    # Pattern: +1 for odd-indexed slack vars, -1 for even, 0 for binary vars
    objective_coeffs = [1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1] + [0] * 60

    # Set objective (minimization)
    model.objective = quicksum(objective_coeffs[j] * all_vars[j] for j in range(74))

    return model


@pytest.fixture()
def infeasible_model() -> Model:
    """Create a simple infeasible model."""
    model = Model("infeasible_model")
    with model.environment:
        x = Variable("x", vtype=Vtype.Integer)

    # Add contradictory constraints
    model.constraints += x >= 10
    model.constraints += x <= 5
    model.objective = 1 * x  # Convert to expression

    return model


@pytest.fixture()
def regular_model() -> Model:
    """Create a simple solvable model."""
    model = Model("regular_model")
    with model.environment:
        x = Variable("x")
        y = Variable("y")

    model.objective = x + y
    model.constraints += x >= 0
    model.constraints += y >= 0
    model.constraints += x + y <= 10

    return model
