from .run_error import RunError


class RunMetricMissingError(RunError):
    """Raised when a metric, a user runs, is missing inside a benchmark."""

    def __init__(self, metric_name: str, benchmark_name: str) -> None:
        self.feature_name = metric_name
        self.benchmark_name = benchmark_name
        super().__init__(
            f"Metric '{metric_name}' is missing in benchmark '{benchmark_name}'."
            f"To solve this issue please add the metric to the benchmark."
        )
