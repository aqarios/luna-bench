from luna_bench.errors.run_errors.run_error import RunError


class PlotRunError(RunError):
    """
    Base exception class for all plot-related runtime errors.

    This exception serves as the parent class for specific plot errors,
    such as missing metrics or features during plot generation.
    """
