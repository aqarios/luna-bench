from luna_quantum import Logging, Model, Variable, Vtype, quicksum
from luna_quantum import Model, Sense, Variable, Vtype, Bounds
from luna_bench.components.benchmark import Benchmark

from luna_bench.components.features import ObjectiveFunctionFeature
from luna_bench.components.features.linear_constraint_matrix import LinearConstraintMatrixFeatures
from luna_bench.components.features.problem_size_feature import ProblemSizeFeatures
from luna_bench.components.features.right_hand_side_feature import RightHandSideFeatures
from luna_bench.components.features.variable_constraint_graph_feature import VariableConstraintGraphFeatures
from luna_bench.components.model_set import ModelSet
import numpy as np


def create_example_model(seed: int = 42) -> Model:
    """
    Create an example optimization model for testing objective function features.

    This model includes all variable types (Real, Integer, Binary, Spin), both positive
    and negative objective function coefficients, and various constraint types to
    demonstrate the full functionality of objective function feature extraction.

    Parameters
    ----------
    seed : int, optional
        Random seed for reproducible coefficient generation, by default 42.

    Returns
    -------
    Model
        A luna_quantum Model instance with diverse variable types, objective coefficients,
        and constraints.

    Examples
    --------
    >>> model = create_example_model(seed=123)
    >>> print(model)
    >>> result = ObjectiveFunctionFeature().run(model)
    """
    rng = np.random.default_rng(seed)

    # Create the model
    model = Model("ObjectiveFunctionFeatureExample")
    model.set_sense(Sense.Min)

    # Define variables of all types within the model's environment
    with model.environment:
        # Real variables with bounds
        x1 = Variable("x1", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=10))
        x2 = Variable("x2", vtype=Vtype.Real, bounds=Bounds(lower=-5, upper=5))
        x3 = Variable("x3", vtype=Vtype.Real, bounds=Bounds(lower=0, upper=20))

        # Integer variables with bounds
        y1 = Variable("y1", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=10))
        y2 = Variable("y2", vtype=Vtype.Integer, bounds=Bounds(lower=-3, upper=7))
        y3 = Variable("y3", vtype=Vtype.Integer, bounds=Bounds(lower=0, upper=15))

        # Binary variables
        b1 = Variable("b1", vtype=Vtype.Binary)
        b2 = Variable("b2", vtype=Vtype.Binary)
        b3 = Variable("b3", vtype=Vtype.Binary)

    # Generate random coefficients with both positive and negative values
    coef_x1 = rng.uniform(1, 10)  # Positive
    coef_x2 = rng.uniform(-8, -1)  # Negative
    coef_x3 = rng.uniform(2, 15)  # Positive
    coef_y1 = rng.uniform(-10, -2)  # Negative
    coef_y2 = rng.uniform(3, 12)  # Positive
    coef_y3 = rng.uniform(-6, -1)  # Negative
    coef_b1 = rng.uniform(5, 20)  # Positive
    coef_b2 = rng.uniform(-15, -3)  # Negative
    coef_b3 = rng.uniform(8, 18)  # Positive


    # Create objective function with mixed positive and negative coefficients
    model.objective = (
        coef_x1 * x1  # Real, positive
        + coef_x2 * x2  # Real, negative
        + coef_x3 * x3  # Real, positive
        + coef_y1 * y1  # Integer, negative
        + coef_y2 * y2  # Integer, positive
        + coef_y3 * y3  # Integer, negative
        + coef_b1 * b1  # Binary, positive
        + coef_b2 * b2  # Binary, negative
        + coef_b3 * b3  # Binary, positive
        + 0.5 * x1 * x2  # Quadratic term (optional)
        + 0.3 * y1 * b1  # Mixed quadratic term (optional)
    )

    # Add various constraints
    # Single variable constraints
    model.constraints += x1 >= 2, "x1_lower"
    model.constraints += x3 <= 15, "x3_upper"
    model.constraints += y1 >= 1, "y1_lower"
    model.constraints += y2 <= 5, "y2_upper"

    # Two-variable constraints
    model.constraints += x1 + x2 >= 0, "real_sum_lower"
    model.constraints += y1 - y2 <= 3, "int_diff_upper"
    model.constraints += x1 - y1 >= 0, "mixed_real_int"

    # Multi-variable constraints
    model.constraints += x1 + x2 + x3 <= 25, "real_sum_constraint"
    model.constraints += y1 + y2 + y3 >= -5, "int_sum_constraint"
    model.constraints += b1 + b2 + b3 >= 1, "binary_at_least_one"
    model.constraints += x1 + 2 * y1 + 3 * b1 <= 30, "mixed_constraint"


    return model



t_f = ObjectiveFunctionFeature()
print('Objective function features:')
print(t_f.run(create_example_model(seed=42)))
t_problem_size = ProblemSizeFeatures()

print('Problem size features:')
print(t_problem_size.run(create_example_model(seed=42)))
t_right_hand_side = RightHandSideFeatures()

print('Right hand side features:')
print(t_right_hand_side.run(create_example_model(seed=42)))
t_variable_constraint_graph = VariableConstraintGraphFeatures()

print('Variable constraint graph features:')
print(t_variable_constraint_graph.run(create_example_model(seed=42)))
t_linear_constraint_matrix = LinearConstraintMatrixFeatures()

print('Linear constraint matrix features:')
print(t_linear_constraint_matrix.run(create_example_model(seed=42)))


model_set = ModelSet.create("test")
model_set.add(model=create_example_model(seed=42))
b = Benchmark.create("xD")
b.set_modelset(model_set)
b.add_feature("cool_name", ObjectiveFunctionFeature())
b.run_features()
print('features')
print(b.features)
