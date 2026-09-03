from luna_bench.errors.components.algorithms.algorithm_error import AlgorithmError


class UnknownParameterPathError(AlgorithmError):
    """Error raised when a variant names a parameter the algorithm does not have."""

    def __init__(self, path: str, algorithm_name: str, available: list[str]) -> None:
        super().__init__(
            f"Algorithm {algorithm_name!r} has no parameter {path!r}. "
            f"Available at that level: {', '.join(sorted(available)) or 'nothing'}."
        )
