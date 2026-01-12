from enum import Enum


class AlgorithmType(str, Enum):
    """Enum for the type of algorithm."""

    SYNC = "SYNC"
    ASYNC = "ASYNC"
