from enum import Enum


class UseCaseErrorHandlingMode(Enum):
    FAIL_ON_ERROR = 0
    CONTINUE_ON_ERROR = 1
