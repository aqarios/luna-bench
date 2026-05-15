from __future__ import annotations

from enum import StrEnum


class Aggregation(StrEnum):
    """Aggregation strategy for metric bar charts.

    The enum values correspond to pandas aggregation function names,
    used directly by seaborn's ``estimator`` parameter.
    """

    MEAN = "mean"
    MEAN_SD = "mean_sd"
    MAX = "max"
    MIN = "min"

    @property
    def estimator(self) -> str:
        """Pandas aggregation function name passed to seaborn."""
        if self is Aggregation.MEAN_SD:
            return "mean"
        return self.value

    @property
    def errorbar(self) -> str | None:
        """Seaborn ``errorbar`` parameter (``"sd"`` or ``None``)."""
        if self is Aggregation.MEAN_SD:
            return "sd"
        return None
