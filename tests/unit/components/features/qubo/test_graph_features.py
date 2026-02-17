"""Tests for QuboGraphFeature."""

import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.graph_features import (
    QuboGraphFeature,
)

from .run_with_matrix import run_with_matrix


class TestQuboGraphFeature:
    """Tests for the QuboGraphFeature extractor."""

    feature = QuboGraphFeature(include_self_loops=False)

    def test_fully_connected_graph_features(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        """Test all features for the fully connected 3x3 QUBO matrix (no self-loops).

        Matrix: [[1,2,3],[2,4,5],[3,5,6]] -> diagonal zeroed -> [[0,2,3],[2,0,5],[3,5,0]]
        Graph: 3 nodes, 3 inter-node edges. Each node has degree 2.
        """
        result = run_with_matrix(fully_connected_qubo_matrix, feature=self.feature)

        # each node connects to the other two
        assert result.average_degree_distribution == pytest.approx(2.0)
        # Weighted clustering on a complete 3-node graph with weights 2, 3, 5
        assert result.average_clustering_coefficient == pytest.approx(0.6214465012, rel=1e-6)
        # All nodes are connected
        assert result.num_connected_components == 1
        # Direct edge between every pair, so shortest path is always 1 hop
        assert result.average_path_length == pytest.approx(1.0)
        # nx.density = 2*|E| / (n*(n-1)) = 2*3 / (3*2) = 1.0 (complete graph)
        assert result.density == pytest.approx(1.0)
        # No bridges or articulation points in a complete graph
        assert result.num_bridges == 0
        assert result.num_articulation_points == 0

    def test_diagonal_matrix_graph_properties(self, diagonal_qubo_matrix: NDArray[np.float64]) -> None:
        """Test features for a diagonal 3x3 matrix with self-loops removed.

        Matrix: [[2,0,0],[0,3,0],[0,0,5]] -> diagonal zeroed -> all zeros.
        Graph: 3 isolated nodes, no edges.
        """
        result = run_with_matrix(diagonal_qubo_matrix, feature=self.feature)

        # All nodes are isolated after removing self-loops
        assert result.num_connected_components == 3
        # No edges at all -> density is 0
        assert result.density == pytest.approx(0.0)

    def test_average_degree_distribution_for_known_matrix(self) -> None:
        """Test degree distribution for a 2x2 matrix with self-loops removed.

        Matrix: [[1,3],[3,2]] -> diagonal zeroed -> [[0,3],[3,0]]
        Graph: 2 nodes, 1 edge. Each node has degree 1.
        """
        matrix = np.array([[1.0, 3.0], [3.0, 2.0]])
        result = run_with_matrix(matrix, feature=self.feature)

        assert result.average_degree_distribution == pytest.approx(1.0)

    def test_graph_with_bridge(self) -> None:
        """Test bridge/articulation detection on a chain graph 0--1--2.

        Matrix: [[0,1,0],[1,0,1],[0,1,0]]
        Graph: 3 nodes, 2 edges, no self-loops. Linear chain topology.
        """
        matrix = np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 1.0],
                [0.0, 1.0, 0.0],
            ]
        )
        result = run_with_matrix(matrix, feature=self.feature)

        assert result.num_connected_components == 1
        # Both edges (0-1) and (1-2) are bridges — removing either disconnects the graph
        assert result.num_bridges == 2
        # Node 1 is the only articulation point — removing it splits the graph into {0} and {2}
        assert result.num_articulation_points == 1

    def test_deterministic_results(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result1 = run_with_matrix(fully_connected_qubo_matrix, feature=self.feature)
        result2 = run_with_matrix(fully_connected_qubo_matrix, feature=self.feature)

        assert result1 == result2
