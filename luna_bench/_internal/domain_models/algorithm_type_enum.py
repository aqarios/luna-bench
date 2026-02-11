from enum import StrEnum


class AlgorithmType(StrEnum):
    """Enum for the type of algorithm."""

    SYNC = "SYNC"
    ASYNC = "ASYNC"
