from luna_bench.errors.decorators.decorator_error import DecoratorError


class InvalidReturnTypeError(DecoratorError):
    """Raised when a function return type does not match the expected type."""

    def __init__(self, func_name: str, expected_type: type, got_type: type) -> None:
        """Initialize the error with function and type information.

        Parameters
        ----------
        func_name : str
            Name of the function with invalid return type.
        expected_type : type
            Expected return type.
        got_type : type
            Actual return type.
        """
        self.func_name = func_name
        self.expected_type = expected_type
        self.got_type = got_type
        message = f"{func_name} must return a {expected_type.__name__}, got {got_type.__name__}"
        super().__init__(message)
