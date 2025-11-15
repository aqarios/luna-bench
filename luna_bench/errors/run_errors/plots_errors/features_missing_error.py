from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError


class FeaturesMissingError(PlotRunError):
    """
    Exception raised when required features are missing from a benchmark.

    This error occurs during plot generation when a plot requires specific
    features that are not present in the benchmark configuration.

    Parameters
    ----------
    features : list[str]
        List of feature names that are required but missing.

    Examples
    --------
    >>> raise FeaturesMissingError(["variable_count", "constraint_count"])
    FeaturesMissingError: Following features missing in benchmark: ['variable_count', 'constraint_count']
    """

    def __init__(self, features: list[str]) -> None:
        """
        Initialize the FeaturesMissingError.

        Parameters
        ----------
        features : list[str]
            List of feature names that are missing from the benchmark.
        """
        super().__init__(f"Following features missing in benchmark: {features}")
