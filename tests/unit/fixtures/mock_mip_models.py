"""Mock MIP models for testing MIP feature extractors."""

import pytest
from luna_quantum import Bounds, Model, Unbounded, Variable, Vtype


@pytest.fixture()
def simple_linear_model() -> Model:
    """
    Create a simple linear programming model with continuous variables.

    Model:
        maximize: 3x + 2y
        subject to: x + y <= 10
                   2x + y >= 5
                   x, y >= 0
    """
    model = Model("simple_linear")

    with model.environment:
        x = Variable("x", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        y = Variable("y", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))

    model.objective = 3 * x + 2 * y
    model.constraints += x + y <= 10
    model.constraints += 2 * x + y >= 5

    return model


@pytest.fixture()
def mixed_integer_model() -> Model:
    """
    Create a mixed-integer programming model.

    Model with binary, integer, and continuous variables.
    """
    model = Model("mixed_integer")

    with model.environment:
        # Binary variables
        b1 = Variable("b1", vtype=Vtype.Binary)
        b2 = Variable("b2", vtype=Vtype.Binary)

        # Integer variables
        i1 = Variable("i1", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))
        i2 = Variable("i2", vtype=Vtype.Integer, bounds=Bounds(lower=Unbounded, upper=Unbounded))

        # Continuous variables
        c1 = Variable("c1", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        c2 = Variable("c2", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=100))

    model.objective = 5 * b1 + 3 * b2 + 2 * i1 + 4 * i2 + c1 + 6 * c2
    model.constraints += b1 + b2 + i1 <= 15
    model.constraints += i1 + i2 + c1 >= 3
    model.constraints += b1 + c1 + c2 == 8
    model.constraints += 2 * b2 + 3 * i1 + c2 <= 20

    return model


@pytest.fixture()
def quadratic_model() -> Model:
    """
    Create a model with quadratic constraints.

    Model with both linear and quadratic constraints.
    """
    model = Model("quadratic")

    with model.environment:
        x = Variable("x", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        y = Variable("y", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        z = Variable("z", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))

    model.objective = x + 2 * y + z

    # Linear constraints
    model.constraints += x + y <= 10
    model.constraints += y + z >= 2

    # Quadratic constraints
    model.constraints += x * x + y * y <= 25
    model.constraints += x * y + z * z <= 15

    return model


@pytest.fixture()
def empty_model() -> Model:
    """Create an empty model with no variables or constraints."""
    return Model("empty")


@pytest.fixture()
def sparse_model() -> Model:
    """
    Create a model with sparse constraint matrix.

    Model with many variables but sparse constraints.
    """
    model = Model("sparse")

    with model.environment:
        variables = [Variable(f"x{i}", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded)) for i in range(10)]

    # Sparse objective (only some variables)
    model.objective = 2 * variables[0] + 3 * variables[5] + variables[9]

    # Sparse constraints
    model.constraints += variables[0] + variables[1] <= 5
    model.constraints += variables[5] + variables[6] + variables[7] >= 3
    model.constraints += variables[9] == 1


    return model


@pytest.fixture()
def dense_model() -> Model:
    """
    Create a model with dense constraint matrix.

    Model where most variables appear in most constraints.
    """
    model = Model("dense")

    with model.environment:
        x1 = Variable("x1", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        x2 = Variable("x2", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        x3 = Variable("x3", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))
        x4 = Variable("x4", vtype=Vtype.Binary)

    model.objective = x1 + 2 * x2 + 3 * x3 + 4 * x4

    # Dense constraints - all variables appear in most constraints
    model.constraints += x1 + x2 + x3 + x4 <= 10
    model.constraints += 2 * x1 + x2 + 2 * x3 + x4 >= 5
    model.constraints += x1 + 3 * x2 + x3 + 2 * x4 == 7
    model.constraints += 4 * x1 + x2 + x3 + x4 <= 15


    return model


@pytest.fixture()
def unbounded_variables_model() -> Model:
    """Create a model with unbounded non-continuous variables."""
    model = Model("unbounded_vars")

    with model.environment:
        # Unbounded integer variable
        i1 = Variable("i1", vtype=Vtype.Integer, bounds=Bounds(lower=Unbounded, upper=Unbounded))
        i2 = Variable("i2", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=Unbounded))

        # Bounded integer variable
        i3 = Variable("i3", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))

        # Continuous variables
        c1 = Variable("c1", vtype=Vtype.Real, bounds=Bounds(lower=Unbounded, upper=Unbounded))

    model.objective = i1 + i2 + i3 + c1
    model.constraints += i1 + i2 <= 10
    model.constraints += i2 + i3 >= 5

    return model


@pytest.fixture()
def all_constraint_types_model() -> Model:
    """Create a model with all constraint types (<=, ==, >=)."""
    model = Model("all_constraints")

    with model.environment:
        x = Variable("x", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        y = Variable("y", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        z = Variable("z", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))

    model.objective = x + y + z

    # Different constraint types
    model.constraints += x + y <= 10
    model.constraints += 2 * x + z <= 15
    model.constraints += y + z == 5
    model.constraints += x + 2 * y == 8
    model.constraints += x + z >= 3
    model.constraints += 2 * y + z >= 4

    return model


@pytest.fixture()
def zero_coefficient_model() -> Model:
    """Create a model with some zero coefficients for edge case testing."""
    model = Model("zero_coef")

    with model.environment:
        x = Variable("x", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        y = Variable("y", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=Unbounded))
        z = Variable("z", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))

    # Objective with all variables
    model.objective = x + 2 * y + 3 * z

    # Constraints with varying sparsity
    model.constraints += x <= 10  # Only x
    model.constraints += y + z >= 5  # y and z, but not x
    model.constraints += x + y + z == 15  # All variables

    return model
