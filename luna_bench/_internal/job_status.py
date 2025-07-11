from enum import Enum


class JobStatus(Enum):
    READY = 0
    RUNNING = 1
    DONE = 2
    FAILED = 3
    ERROR = 4
