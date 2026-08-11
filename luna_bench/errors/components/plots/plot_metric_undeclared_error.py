from luna_bench.errors.components.plots.plot_error import PlotError


class PlotMetricUndeclaredError(PlotError):
    """Error raised when a metric bar plot does not declare the metric it reads."""

    def __init__(self, plot_class_name: str) -> None:
        super().__init__(
            f"Plot {plot_class_name!r} reads a metric but declares none. "
            f"Decorate it with the metric it needs, e.g. '@plot(Runtime)'."
        )
