from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError


class PlotExecutionError(PlotRunError):
    """Exception raised when there is an error during plot execution."""

    error: Exception

    def __init__(self, benchmark_name: str, plot_name: str, error: Exception) -> None:
        super().__init__(f"Benchmark '{benchmark_name}' failed to execute plot '{plot_name}'. Error {error!r}")
        self.error = error
