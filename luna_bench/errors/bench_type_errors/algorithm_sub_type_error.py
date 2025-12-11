from luna_bench.errors.bench_type_errors.bench_type_error import BenchTypeError


class AlgorithmSubTypeError(BenchTypeError):
    """Error raised when an algorithm is of the wrong type."""

    def __init__(self, algorithm_type: str) -> None:
        super().__init__(f"Algorithm type must be a subtype of {algorithm_type}.")
