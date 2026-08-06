from __future__ import annotations

from enum import StrEnum

from .errorbar import ErrorBar


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
    def errorbar(self) -> ErrorBar:
        """Default seaborn ``errorbar`` parameter for this aggregation.

        Means carry the spread of the underlying samples (``"sd"``); extrema are
        single observations, so they get no error bar.
        """
        if self in (Aggregation.MEAN, Aggregation.MEAN_SD):
            return "sd"
        return None
