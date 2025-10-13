from .run_error import RunError


class RunFeatureMissingError(RunError):
    """Raised when a feature, a user runs, is missing inside a benchmark."""

    def __init__(self, feature_name: str, benchmark_name: str) -> None:
        self.feature_name = feature_name
        self.benchmark_name = benchmark_name
        super().__init__(
            f"Feature '{feature_name}' is missing in benchmark '{benchmark_name}'."
            f"To solve this issue please add the feature to the benchmark."
        )
