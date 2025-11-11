from .run_error import RunError


class RunAlgorithmMissingError(RunError):
    """Raised when an algorithm, a user runs, is missing inside a benchmark."""

    def __init__(self, algorithm_name: str, benchmark_name: str) -> None:
        self.algorithm_name = algorithm_name
        self.benchmark_name = benchmark_name
        super().__init__(
            f"Algorithm '{algorithm_name}' is missing in benchmark '{benchmark_name}'."
            f"To solve this issue please add the algorithm to the benchmark."
        )
