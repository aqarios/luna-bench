from .run_error import RunError


class RunPlotMissingError(RunError):
    """Raised when a plot, a user runs, is missing inside a benchmark."""

    def __init__(self, plot_name: str, benchmark_name: str) -> None:
        self.plot_name = plot_name
        self.benchmark_name = benchmark_name
        super().__init__(
            f"Plot '{plot_name}' is missing in benchmark '{benchmark_name}'."
            f"To solve this issue please add the plot to the benchmark."
        )
