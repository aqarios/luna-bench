from luna_bench.errors.decorators.decorator_error import DecoratorError


class InvalidParameterTypeError(DecoratorError):
    """Raised when a function parameter type does not match the expected type."""

    def __init__(self, param_name: str, func_name: str, expected_type_name: str, got_type_name: str) -> None:
        """Initialize the error with parameter and type information.

        Parameters
        ----------
        param_name : str
            Name of the parameter with invalid type.
        func_name : str
            Name of the function containing the parameter.
        expected_type_name : str
            Name of the expected type.
        got_type_name : str
            Name of the actual type.
        """
        self.param_name = param_name
        self.func_name = func_name
        self.expected_type_name = expected_type_name
        self.got_type_name = got_type_name
        message = f"Parameter '{param_name}' in '{func_name}' must be of type {expected_type_name}, got {got_type_name}"
        super().__init__(message)
