from .base_error import BaseError


class InfeasibleModelError(BaseError):
    """
    Exception raised when a model solved by SCIP is identified as infeasible.

    This indicates that no feasible solution exists for the given constraints.
    """

    def __init__(self) -> None:
        super().__init__("Model is infeasible. No solution possible.")
