from enum import StrEnum


class ResetLevel(StrEnum):
    """Level of reset granularity for benchmark results.

    Controls which results are cleared when resetting a benchmark.

    - ALL: Clear all results unconditionally.
    - UNFINISHED: Clear only results whose status is not DONE
      (i.e. CREATED, UPDATED, RUNNING, FAILED).
      This includes failed components.
    - FAILED: Clear only results whose status is FAILED.
    """

    ALL = "All"
    UNFINISHED = "Unfinished"
    FAILED = "Failed"
