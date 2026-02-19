"""QUBO matrix fixtures for testing QUBO feature extractors."""

import numpy as np
import pytest
from numpy.typing import NDArray


@pytest.fixture()
def sample_qubo_matrix() -> NDArray[np.float64]:
    """Create a 3x3 symmetric QUBO matrix with some zero entries."""
    return np.array(
        [
            [1.0, 2.0, 0.0],
            [2.0, 3.0, 1.0],
            [0.0, 1.0, 4.0],
        ]
    )


@pytest.fixture()
def fully_connected_qubo_matrix() -> NDArray[np.float64]:
    """Create a 3x3 fully connected symmetric QUBO matrix (no zeros)."""
    return np.array(
        [
            [1.0, 2.0, 3.0],
            [2.0, 4.0, 5.0],
            [3.0, 5.0, 6.0],
        ]
    )


@pytest.fixture()
def diagonal_qubo_matrix() -> NDArray[np.float64]:
    """Create a 3x3 diagonal matrix (only self-loops, no cross-variable interactions)."""
    return np.array(
        [
            [2.0, 0.0, 0.0],
            [0.0, 3.0, 0.0],
            [0.0, 0.0, 5.0],
        ]
    )
