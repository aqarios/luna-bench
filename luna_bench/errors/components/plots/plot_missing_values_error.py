from luna_bench.errors.components.plots.plot_error import PlotError


class PlotMissingValuesError(PlotError):
    """Error raised when a plot is asked to draw values it has none of.

    Raised under ``Missing(policy="raise")``, for a benchmark where a metric that reported
    nothing - an infinite time to solution, a ratio it could not compute - means the run
    itself went wrong. Every other policy carries on and says on the figure what it did,
    because carrying on quietly changes what the figure means: dropping the values shows an
    average over fewer models than it claims, filling them puts a number on the axis that
    no run produced. Which of them happens is what ``Missing`` is for.
    """

    def __init__(self, plot_class_name: str, column: str, count: int, total: int, categories: str) -> None:
        super().__init__(
            f"Plot {plot_class_name!r} cannot draw {count} of {total} values of {column!r} "
            f"({categories}): they are missing or not finite. "
            f"Choose what should happen to them, e.g. 'missing=Missing(policy=\"drop\")' to "
            f"leave them out, or 'missing=Missing(policy=\"max\")' to draw them just past "
            f"the largest value that could be drawn."
        )
