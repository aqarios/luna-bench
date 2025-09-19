from enum import Enum


class BenchmarkStatus(str, Enum):
    """Enum for the status of a benchmark."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    INVALID = "INVALID"
