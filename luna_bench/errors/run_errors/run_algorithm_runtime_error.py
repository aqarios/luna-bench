from .run_error import RunError


class RunAlgorithmRuntimeError(RunError):
    """Raised when an algorithm, a user runs, is raising an exception."""

    def __init__(self, exception: Exception) -> None:
        self.exception = exception
        super().__init__("An algorithm raised an exception while being executed.")

    def error(self) -> Exception:
        """Get the exception which was wrapped."""
        return self.exception
