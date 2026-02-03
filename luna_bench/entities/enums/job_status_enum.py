from enum import Enum


class JobStatus(str, Enum):
    """Enum for the status of a job."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
