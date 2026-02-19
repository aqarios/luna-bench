import numpy as np
from numpy._typing import NDArray
from scipy.stats import kurtosis as scipy_kurtosis
from scipy.stats import skew as scipy_skew


class NumpyStatsHelper:
    """Helper class for calculating statistical measures of numpy arrays."""

    @staticmethod
    def mean(data: NDArray[np.float64]) -> np.float64:
        """Calculate the mean of the array, returning 0 if empty."""
        return data.mean() if len(data) != 0 else np.float64(0)

    @staticmethod
    def std(data: NDArray[np.float64]) -> np.float64:
        """Calculate the standard deviation of the array, returning 0 if empty."""
        return data.std() if len(data) != 0 else np.float64(0)

    @staticmethod
    def var(data: NDArray[np.float64]) -> np.float64:
        """Calculate the variance of the array, returning 0 if empty."""
        return data.var() if len(data) != 0 else np.float64(0)

    @staticmethod
    def normalized(data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Normalize the array by dividing by its sum."""
        return data / np.sum(data) if np.sum(data) != 0 else data

    @staticmethod
    def sqrt_normalized(data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Normalize the array and then apply square root."""
        data = data / np.sum(data) if np.sum(data) != 0 else data
        return np.sqrt(data)

    @staticmethod
    def median(data: NDArray[np.float64]) -> float:
        """Calculate the median of the array, returning 0 if empty."""
        return np.median(data).item() if len(data) != 0 else np.float64(0)

    @staticmethod
    def vc(data: NDArray[np.float64]) -> np.float64:
        """Calculate the coefficient of variation (std/mean), returning 0 if empty or mean is 0."""
        if len(data) == 0:
            return np.float64(0)

        std = data.std()
        mean = data.mean()

        if mean == 0:
            return np.float64(0)

        return np.float64(std / mean)

    @staticmethod
    def q10(data: NDArray[np.float64]) -> float:
        """Calculate the 10th percentile, returning 0 if empty."""
        if len(data) == 0:
            return 0
        return np.percentile(data, 10).item()

    @staticmethod
    def q90(data: NDArray[np.float64]) -> float:
        """Calculate the 90th percentile, returning 0 if empty."""
        if len(data) == 0:
            return 0
        return np.percentile(data, 90).item()

    @staticmethod
    def skew(data: NDArray[np.float64]) -> float:
        """Calculate the skewness of the array, returning 0 if empty."""
        if len(data) == 0:
            return 0.0
        return float(scipy_skew(data))

    @staticmethod
    def kurtosis(data: NDArray[np.float64]) -> float:
        """Calculate the excess kurtosis of the array, returning 0 if empty."""
        if len(data) == 0:
            return 0.0
        return float(scipy_kurtosis(data))

    @staticmethod
    def min(data: NDArray[np.float64]) -> float:
        """Calculate the minimum value of the array."""
        return np.min(data)

    @staticmethod
    def max(data: NDArray[np.float64]) -> float:
        """Calculate the maximum value of the array."""
        return np.max(data)
