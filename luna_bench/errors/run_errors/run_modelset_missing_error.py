from .run_error import RunError


class RunModelsetMissingError(RunError):
    """Base class for errors related to running a benchmark or single components and there is no modelset configured."""

    def __init__(self, benchmark_name: str) -> None:
        self.benchmark_name = benchmark_name
        super().__init__(
            f"No modelset is configured for benchmark '{benchmark_name}'. To run any component you first "
            f"need to configure a modelset and add at least one model to the modelset."
        )
