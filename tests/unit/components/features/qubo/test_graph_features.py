"""Tests for QuboGraphFeature."""

from unittest.mock import MagicMock, patch

import networkx as nx
import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.graph_features import (
    QuboGraphFeature,
    QuboGraphFeatureResult,
)


class TestQuboGraphFeature:
    """Tests for the QuboGraphFeature extractor."""

    @staticmethod
    def _run_with_matrix(matrix: NDArray[np.float64]) -> QuboGraphFeatureResult:
        mock_model = MagicMock()
        with patch(
            "luna_bench.components.features.qubo.graph_features.get_qubo",
            return_value=matrix,
        ):
            return QuboGraphFeature().run(mock_model)

    def test_returns_correct_result_type(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        assert isinstance(result, QuboGraphFeatureResult)

    def test_all_fields_populated(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)

        assert result.average_degree_distribution is not None
        assert result.average_clustering_coefficient is not None
        assert result.num_connected_components is not None
        assert result.average_path_length is not None
        assert result.density is not None
        assert result.num_bridges is not None
        assert result.num_articulation_points is not None

    def test_fully_connected_graph_has_one_component(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        assert result.num_connected_components == 1

    def test_fully_connected_graph_density(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        # nx.density counts self-loops as edges, so density > 1.0 for QUBO matrices with non-zero diagonal
        graph = nx.from_numpy_array(fully_connected_qubo_matrix)
        assert result.density == pytest.approx(nx.density(graph))

    def test_fully_connected_graph_has_no_bridges(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        assert result.num_bridges == 0

    def test_fully_connected_graph_has_no_articulation_points(
        self, fully_connected_qubo_matrix: NDArray[np.float64]
    ) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        assert result.num_articulation_points == 0

    def test_diagonal_matrix_graph_properties(self, diagonal_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(diagonal_qubo_matrix)

        # Diagonal matrix → no edges between nodes (only self-loops)
        # Self-loops make each node its own connected component
        assert result.num_connected_components == 3
        # nx.density counts self-loops, so density is not 0 even with only self-loops
        graph = nx.from_numpy_array(diagonal_qubo_matrix)
        assert result.density == pytest.approx(nx.density(graph))

    def test_average_degree_distribution_for_known_matrix(self) -> None:
        # 2x2 matrix with one off-diagonal connection
        matrix = np.array([[1.0, 3.0], [3.0, 2.0]])
        result = self._run_with_matrix(matrix)

        # Graph: 2 nodes, 1 edge, self-loops on each
        # nx.from_numpy_array with self-loops: degree includes self-loop weight
        graph = nx.from_numpy_array(matrix)
        expected_avg_degree = np.mean([d for _, d in graph.degree()])
        assert result.average_degree_distribution == pytest.approx(expected_avg_degree)

    def test_graph_with_bridge(self) -> None:
        # Chain graph: 0 -- 1 -- 2 (edges 0-1 and 1-2 are bridges, node 1 is articulation point)
        matrix = np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 1.0],
                [0.0, 1.0, 0.0],
            ]
        )
        result = self._run_with_matrix(matrix)

        assert result.num_connected_components == 1
        assert result.num_bridges == 2
        assert result.num_articulation_points == 1

    def test_average_path_length_for_connected_graph(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        # In a complete graph with 3 nodes, shortest path length between any two nodes is 1
        assert result.average_path_length == pytest.approx(1.0)

    def test_average_clustering_coefficient_complete_graph(
        self, fully_connected_qubo_matrix: NDArray[np.float64]
    ) -> None:
        result = self._run_with_matrix(fully_connected_qubo_matrix)
        # Weighted clustering coefficient differs from unweighted due to self-loops and weights
        graph = nx.from_numpy_array(fully_connected_qubo_matrix)
        expected = nx.average_clustering(graph, weight="weight")
        assert result.average_clustering_coefficient == pytest.approx(expected)

    def test_deterministic_results(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result1 = self._run_with_matrix(fully_connected_qubo_matrix)
        result2 = self._run_with_matrix(fully_connected_qubo_matrix)

        assert result1.average_degree_distribution == result2.average_degree_distribution
        assert result1.num_connected_components == result2.num_connected_components
        assert result1.density == result2.density
