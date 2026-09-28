from luna_bench.errors.components.algorithms.algorithm_error import AlgorithmError


class MetadataNotAvailableError(AlgorithmError):
    """
    Raised when metadata is read for a run whose algorithm reported none.

    An algorithm returns metadata by returning ``(solution, metadata)`` instead of a bare
    ``Solution``. One that returns only the solution leaves the metadata empty, and every
    read of its content raises this error rather than pretending an empty mapping was
    reported.
    """

    def __init__(self) -> None:
        super().__init__(
            "No metadata is available for this run. An algorithm reports metadata by returning "
            "(solution, metadata) from its run method; one that returns the solution alone "
            "reports none. Check SolveMetadata.available before reading it."
        )
