from enum import Enum


class ErrorHandlingMode(Enum):
    """
    Determines behavior when plot validation or execution fails.

    - FAIL_ON_ERROR: Stop at the first error and raise RuntimeError
    - CONTINUE_ON_ERROR: Log warnings and continue with remaining plots
    """

    FAIL_ON_ERROR = 0
    CONTINUE_ON_ERROR = 1
