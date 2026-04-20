from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

from .get_qubo import get_qubo

if TYPE_CHECKING:
    from luna_model import Model


class QuboGraphFeatureResult(ArbitraryDataDomain):
    """Result container for graph-based QUBO features.

    The QUBO matrix is interpreted as a weighted adjacency matrix via
    ``networkx.from_numpy_array``. Non-zero diagonal entries become self-loops
    and non-zero off-diagonal entries become weighted edges.

    Attributes
    ----------
    self_loops : bool
        Whether diagonal elements (self-loops) were included in the graph
        analysis. If False, only variable interactions were analyzed. If True,
        linear terms were included as self-loops.
    average_degree_distribution : float
        Mean node degree across all nodes. The degree of a node is the number
        of edges incident to it. In networkx, a self-loop contributes 2 to a
        node's degree (both endpoints are the same node), so values can exceed
        the number of inter-node edges.
    average_clustering_coefficient : float
        Weighted clustering coefficient averaged over all nodes. Measures the
        fraction of possible triangles through a node that actually exist,
        i.e. how strongly a node's neighbours tend to be connected to each
        other. A value of 1.0 means all neighbours are fully interconnected;
        0.0 means none are. Because ``weight="weight"`` is used, triangle
        contributions are scaled by the geometric mean of the involved edge
        weights.
    num_connected_components : int
        Number of connected components in the QUBO interaction graph.
        A fully connected QUBO has 1 component (lower bound), meaning the
        graph cannot be decomposed further. A purely diagonal QUBO (no
        off-diagonal entries) has n = num_nodes independent components
        (upper bound) as each node is a component. Range: [1, num_nodes of graph].
    average_path_length : float
        Mean shortest-path length computed on the largest connected component.
    density : float
        Graph density defined as ``2 * |E| / (n * (n - 1))``. Can exceed 1.0
        because self-loops are counted as edges but not in the denominator.
    num_bridges : int
        Number of bridge edges whose removal would disconnect the graph.
        Indicates structural fragility.
    num_articulation_points : int
        Number of articulation points (cut vertices) whose removal would
        increase the number of connected components.
    """

    self_loops: bool
    average_degree_distribution: float
    average_clustering_coefficient: float
    num_connected_components: int
    average_path_length: float
    density: float
    num_bridges: int
    num_articulation_points: int


@feature
class QuboGraphFeature(BaseFeature):
    """Extract graph-based features from QUBO models.

    Compute graph-theoretic features from the QUBO matrix by constructing a
    weighted graph via ``networkx.from_numpy_array`` and analysing its topology.

    Extracted features include:

    - **Connectivity**: Average degree distribution, average clustering
      coefficient, number of connected components, and average path length.
    - **Robustness**: Graph density, number of bridges, and number of
      articulation points.

    Attributes
    ----------
    include_self_loops : bool
        Whether to include diagonal elements (self-loops) in the graph analysis.
        If False (default), diagonal entries are zeroed out before constructing
        the graph, analyzing only variable interactions. If True, linear terms
        are included as self-loops, which affects degree calculations and other
        metrics.
    """

    include_self_loops: bool = False

    def run(self, model: Model) -> QuboGraphFeatureResult:
        """Compute graph-based features for the given model.

        Parameters
        ----------
        model : Model
            The optimization model to extract features from.

        Returns
        -------
        QuboGraphFeatureResult
            A result object containing the computed graph features.
        """
        qubo = get_qubo(model)

        if not self.include_self_loops:
            np.fill_diagonal(qubo, 0)

        graph = nx.from_numpy_array(qubo)

        return QuboGraphFeatureResult(
            self_loops=self.include_self_loops,
            average_degree_distribution=NumpyStatsHelper.mean(np.array([d for _, d in graph.degree()])),
            average_clustering_coefficient=nx.average_clustering(graph, weight="weight"),
            num_connected_components=nx.number_connected_components(graph),
            average_path_length=nx.average_shortest_path_length(
                graph.subgraph(max(nx.connected_components(graph), key=len))
            ),
            density=nx.density(graph),
            num_bridges=len(list(nx.bridges(graph))),
            num_articulation_points=len(list(nx.articulation_points(graph))),
        )
