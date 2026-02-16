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
    from luna_quantum import Model


class QuboGraphFeatureResult(ArbitraryDataDomain):
    """Result container for graph-based QUBO features."""

    average_degree_distribution: float
    average_clustering_coefficient: float
    num_connected_components: float
    average_path_length: float
    density: float
    num_bridges: float
    num_articulation_points: float


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
    """

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
        graph = nx.from_numpy_array(qubo)

        return QuboGraphFeatureResult(
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
