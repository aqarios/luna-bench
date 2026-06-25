from enum import StrEnum


class JobStatus(StrEnum):
    """Enum for the status of a job."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
