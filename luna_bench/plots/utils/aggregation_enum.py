from __future__ import annotations

from enum import StrEnum

from .errorbar import ErrorBar


class Aggregation(StrEnum):
    """Aggregation strategy for metric bar charts.

    The enum values correspond to pandas aggregation function names,
    used directly by seaborn's ``estimator`` parameter.
    """

    MEAN = "mean"
    MAX = "max"
    MIN = "min"

    @property
    def estimator(self) -> str:
        """Pandas aggregation function name passed to seaborn."""
        return self.value

    @property
    def errorbar(self) -> ErrorBar:
        """Default seaborn ``errorbar`` parameter for this aggregation.

        Only what the error bar defaults to - an `ErrorBars` says what it actually shows.
        A mean carries the spread of the values it averaged (``"sd"``); an extremum is a
        single observation, so it gets none.
        """
        return "sd" if self is Aggregation.MEAN else None
