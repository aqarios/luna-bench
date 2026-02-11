from enum import StrEnum


class BenchmarkStatus(StrEnum):
    """Enum for the status of a benchmark."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    INVALID = "INVALID"
