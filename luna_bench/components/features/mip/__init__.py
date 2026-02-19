"""
MIP Feature: module provides feature extractors for analyzing Mixed-Integer Programming (MIP) problems.

These extractors compute structural and statistical properties of MIP models that can later be used for algorithm
selection, performance prediction, and problem characterization. The features capture various aspects of MIP problem
structure including constraint matrix properties, objective function characteristics, problem dimensions, right-hand
side distributions, and variable-constraint graph topology.

Usage in Luna Bench
-------------------
To use these feature extractors in your benchmark:

.. code-block:: python

    from luna_bench import Benchmark
    from luna_bench.components.features.mip import ProblemSizeFeatures, LinearConstraintMatrixFeatures

    # Create a benchmark
    b = Benchmark()

    # Add feature extractors
    b.add_feature("problem_size", ProblemSizeFeatures())
    b.add_feature("constraint_matrix", LinearConstraintMatrixFeatures())

    # Features will be automatically extracted when running the benchmark

Available Feature Extractors
-----------------------------
- **LinearConstraintMatrixFeatures**: Analyzes the linear constraint matrix structure, including sparsity patterns,
  coefficient distributions, and matrix properties.
- **ObjectiveFunctionFeatures**: Extracts statistics from objective function coefficients, such as magnitude ranges,
  sign patterns, and distribution characteristics.
- **ProblemSizeFeatures**: Captures problem dimensions including number of variables, constraints, binary/integer
  variables, and structural ratios.
- **RightHandSideFeatures**: Computes distributional properties of constraint right-hand side values, including
  ranges, statistics, and patterns.
- **VariableConstraintGraphFeatures**: Analyzes the bipartite graph connecting variables and constraints, computing
  degree distributions, connectivity metrics, and graph-theoretic properties.

References
----------
Feature definitions based on:
https://www.sciencedirect.com/science/article/pii/S0004370213001082#se0240
"""

from .linear_constraint_matrix import LinearConstraintMatrixFeatures, LinearConstraintMatrixFeaturesResult
from .objective_function_features import ObjectiveFunctionFeature, ObjectiveFunctionFeatureResult
from .problem_size_feature import ProblemSizeFeatures, ProblemSizeFeaturesResult
from .right_hand_side_feature import RightHandSideFeatures, RightHandSideFeaturesResult
from .variable_constraint_graph_feature import VariableConstraintGraphFeatures, VariableConstraintGraphFeaturesResult

__all__ = [
    "LinearConstraintMatrixFeatures",
    "LinearConstraintMatrixFeaturesResult",
    "ObjectiveFunctionFeature",
    "ObjectiveFunctionFeatureResult",
    "ProblemSizeFeatures",
    "ProblemSizeFeaturesResult",
    "RightHandSideFeatures",
    "RightHandSideFeaturesResult",
    "VariableConstraintGraphFeatures",
    "VariableConstraintGraphFeaturesResult",
]
