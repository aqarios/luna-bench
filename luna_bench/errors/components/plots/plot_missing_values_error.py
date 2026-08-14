from luna_bench.errors.components.plots.plot_error import PlotError


class PlotMissingValuesError(PlotError):
    """Error raised when a plot is asked to draw values it has none of.

    The default reaction to a metric that reported nothing - an infinite time to solution,
    a ratio the metric could not compute - because every other reaction quietly changes
    what the figure says: dropping them shows an average over fewer models than it claims,
    filling them puts a number on the axis that no run produced. Both are reasonable once
    they are chosen, which is what ``Missing`` is for.
    """

    def __init__(self, plot_class_name: str, column: str, count: int, total: int, categories: str) -> None:
        super().__init__(
            f"Plot {plot_class_name!r} cannot draw {count} of {total} values of {column!r} "
            f"({categories}): they are missing or not finite. "
            f"Choose what should happen to them, e.g. 'missing=Missing(policy=\"drop\")' to "
            f"leave them out, or 'missing=Missing(policy=\"max\")' to draw them just past "
            f"the largest value that could be drawn."
        )
