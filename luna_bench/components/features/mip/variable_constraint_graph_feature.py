from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from luna_quantum import Vtype
from pydantic import BaseModel

from luna_bench._internal.interfaces import IFeature
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.components.helper.var_scope import VarScope
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model
    from numpy.typing import NDArray

from luna_bench.components.features.base_feature import BaseFeatureResult


class NodeType(str, Enum):
    """Type of node in the variable-constraint bipartite graph."""

    VARIABLE = "variable"  # Variable nodes (column degree)
    CONSTRAINT = "constraint"  # Constraint nodes (row degree)


class NodeDegreeStatsKey(NamedTuple):
    """Key for accessing node degree statistics."""

    node_type: NodeType
    var_scope: VarScope

    @property
    def key(self) -> str:
        """Generate string key from tuple values."""
        return "_".join(v.value for v in self)


class NodeDegreeStats(BaseModel):
    """
    Container for node degree statistics.

    Attributes
    ----------
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

    mean: float
    median: float
    variation_coefficient: float
    q90: float
    q10: float


class VariableConstraintGraphFeaturesResult(BaseFeatureResult[NodeDegreeStatsKey, NodeDegreeStats]):
    """
    Result container for variable-constraint graph feature calculations.

    Access via NodeDegreeStatsKey:
        result.stats[NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=VarScope.CONTINUOUS).key]
    """


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
            stats[str(NodeDegreeStatsKey(node_type=NodeType.VARIABLE, var_scope=var_scope)._asdict())] = (
                self._compute_degree_stats(var_node_degrees)
            )

            # Constraint node degrees (row sums = connections per constraint)
            cons_node_degrees = np.sum(a_binary, axis=1)
            stats[str(NodeDegreeStatsKey(node_type=NodeType.CONSTRAINT, var_scope=var_scope)._asdict())] = (
                self._compute_degree_stats(cons_node_degrees)
            )

        return VariableConstraintGraphFeaturesResult(stats=stats)

    def _compute_degree_stats(self, degrees: NDArray[np.int_]) -> NodeDegreeStats:
        """
        Compute all degree statistics for a given array of node degrees.

        Parameters
        ----------
        degrees : NDArray
            Array of node degrees.

        Returns
        -------
        NodeDegreeStats
            Container with all statistical measures.
        """
        return NodeDegreeStats(
            mean=NumpyStatsHelper.mean(degrees),
            median=NumpyStatsHelper.median(degrees),
            variation_coefficient=NumpyStatsHelper.vc(degrees),
            q90=NumpyStatsHelper.q90(degrees),
            q10=NumpyStatsHelper.q10(degrees),
        )
