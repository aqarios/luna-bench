from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError


class MetricsMissingError(PlotRunError):
    """
    Exception raised when required metrics are missing from a benchmark.

    This error occurs during plot generation when a plot requires specific
    metrics that are not present in the benchmark configuration.

    Parameters
    ----------
    metrics : list[str]
        List of metric names that are required but missing.

    Examples
    --------
    >>> raise MetricsMissingError(["approximation_ratio", "time_to_solution"])
    MetricsMissingError: Following metrics missing in benchmark: ['approximation_ratio', 'time_to_solution']
    """

    def __init__(self, metrics: list[str]) -> None:
        """
        Initialize the MetricsMissingError.

        Parameters
        ----------
        metrics : list[str]
            List of metric names that are missing from the benchmark.
        """
        super().__init__(f"Following metrics missing in benchmark: {metrics}")
