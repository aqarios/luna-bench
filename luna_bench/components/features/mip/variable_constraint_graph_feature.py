from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype
from pydantic import BaseModel

from luna_bench._internal.interfaces import IFeature
from luna_bench.components.features.base_results import BaseStatsResultWithVarScope
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.components.helper.var_scope import VarScope
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model
    from numpy.typing import NDArray


class NodeType(str, Enum):
    """Type of node in the variable-constraint bipartite graph."""

    VARIABLE = "variable"  # Variable nodes (column degree)
    CONSTRAINT = "constraint"  # Constraint nodes (row degree)


class NodeDegreeStats(BaseModel):
    """
    Container for node degree statistics with descriptive context.

    Attributes
    ----------
    node_type : NodeType
        The type of node (variable or constraint).
    var_scope : VarScope
        The scope of variables included (continuous, non_continuous, all).
    mean : float
        Mean node degree.
    median : float
        Median node degree.
    variation_coefficient : float
        Variation coefficient (std/mean) of node degrees.
    q90 : float
        90th percentile of node degrees.
    q10 : float
        10th percentile of node degrees.
    """

    node_type: NodeType
    var_scope: VarScope
    mean: float
    median: float
    variation_coefficient: float
    q90: float
    q10: float


class VariableConstraintGraphFeaturesResult(BaseStatsResultWithVarScope[NodeType, NodeDegreeStats]):
    """
    Result container for variable-constraint graph feature calculations.

    This class stores graph-based statistics for variables and constraints,
    including node degree measures for continuous, non-continuous, and all
    variable/constraint types.

    Access patterns:
        - result.get(NodeType.VARIABLE, VarScope.CONTINUOUS) -> NodeDegreeStats
        - result.get_mean(NodeType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.get_median(NodeType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.get_vc(NodeType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.get_q90(NodeType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.get_q10(NodeType.VARIABLE, VarScope.CONTINUOUS) -> float
        - result.by_type(NodeType.VARIABLE) -> Dict[VarScope, NodeDegreeStats]
        - result.by_scope(VarScope.CONTINUOUS) -> Dict[NodeType, NodeDegreeStats]

    Attributes
    ----------
    stats : Dict[str, NodeDegreeStats]
        Dictionary mapping "{node_type}_{var_scope}" keys to NodeDegreeStats objects.
    """

    @staticmethod
    def _type_enum() -> type[NodeType]:
        """Return the NodeType enum class."""
        return NodeType

    def get_median(self, node_type: NodeType, var_scope: VarScope) -> float:
        """Direct access to median value."""
        return self.get(node_type, var_scope).median

    def get_vc(self, node_type: NodeType, var_scope: VarScope) -> float:
        """Direct access to variation coefficient."""
        return self.get(node_type, var_scope).variation_coefficient

    def get_q90(self, node_type: NodeType, var_scope: VarScope) -> float:
        """Direct access to 90th percentile."""
        return self.get(node_type, var_scope).q90

    def get_q10(self, node_type: NodeType, var_scope: VarScope) -> float:
        """Direct access to 10th percentile."""
        return self.get(node_type, var_scope).q10


@feature
class VariableConstraintGraphFeatures(IFeature):
    """
    Feature extractor for variable-constraint graph properties.

    Calculates node degree statistics for variables and constraints in the
    bipartite graph representation of an optimization model. Computes statistics
    separately for continuous and non-continuous variables/constraints.
    """

    def run(self, model: Model) -> VariableConstraintGraphFeaturesResult:
        """
        Calculate variable-constraint graph features.

        Computes node degree statistics (mean, median, variation coefficient,
        and quantiles) for variables and constraints, grouped by variable type.

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        VariableConstraintGraphFeaturesResult
            Container with graph-based statistical measures.
        """
        stats: dict[str, NodeDegreeStats] = {}

        # Define the variable type configurations
        scope_configs = [
            (VarScope.CONTINUOUS, Vtype.Real),
            (VarScope.NON_CONTINUOUS, [Vtype.Integer, Vtype.Binary]),
            (VarScope.ALL, None),
        ]

        for var_scope, vtype in scope_configs:
            # Get constraint matrix for this variable scope
            a, _ = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=vtype)

            # Convert to binary (non-zero = 1)
            a_binary = (a != 0).astype(int)

            # Variable node degrees (column sums = connections per variable)
            var_node_degrees = np.sum(a_binary, axis=0)
            stats[VariableConstraintGraphFeaturesResult.make_key(NodeType.VARIABLE, var_scope)] = (
                self._compute_degree_stats(NodeType.VARIABLE, var_scope, var_node_degrees)
            )

            # Constraint node degrees (row sums = connections per constraint)
            cons_node_degrees = np.sum(a_binary, axis=1)
            stats[VariableConstraintGraphFeaturesResult.make_key(NodeType.CONSTRAINT, var_scope)] = (
                self._compute_degree_stats(NodeType.CONSTRAINT, var_scope, cons_node_degrees)
            )

        return VariableConstraintGraphFeaturesResult(stats=stats)

    def _compute_degree_stats(
        self,
        node_type: NodeType,
        var_scope: VarScope,
        degrees: NDArray[np.int_],
    ) -> NodeDegreeStats:
        """
        Compute all degree statistics for a given array of node degrees.

        Parameters
        ----------
        node_type : NodeType
            The type of node.
        var_scope : VarScope
            The scope of variables.
        degrees : NDArray
            Array of node degrees.

        Returns
        -------
        NodeDegreeStats
            Container with all statistical measures.
        """
        return NodeDegreeStats(
            node_type=node_type,
            var_scope=var_scope,
            mean=NumpyStatsHelper.mean(degrees),
            median=NumpyStatsHelper.median(degrees),
            variation_coefficient=NumpyStatsHelper.vc(degrees),
            q90=NumpyStatsHelper.q90(degrees),
            q10=NumpyStatsHelper.q10(degrees),
        )
