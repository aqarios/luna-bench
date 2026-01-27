from luna_bench.entities.enums import JobStatus

from .run_error import RunError


class AlgorithmNotDoneError(RunError):
    """Raised when an algorithm, a user runs, is not yet Done but its needed for a a specific step."""

    def __init__(self, algorithm_name: str, status: JobStatus) -> None:
        super().__init__(f"The algorithm '{algorithm_name}' is not yet done. Current status is '{status}'.")
