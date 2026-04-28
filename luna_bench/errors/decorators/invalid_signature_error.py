from luna_bench.errors.decorators.decorator_error import DecoratorError


class InvalidSignatureError(DecoratorError):
    """Raised when a function signature does not match the expected parameters."""

    def __init__(self, func_name: str, expected_params: list[str], got_params: list[str]) -> None:
        """Initialize the error with function and parameter information.

        Parameters
        ----------
        func_name : str
            Name of the function with invalid signature.
        expected_params : list[str]
            Expected parameter names.
        got_params : list[str]
            Actual parameter names.
        """
        self.func_name = func_name
        self.expected_params = expected_params
        self.got_params = got_params
        message = f"Function '{func_name}' must have parameters {expected_params}, got {got_params}"
        super().__init__(message)
