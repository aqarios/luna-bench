from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench._internal.usecases.benchmark.protocols import PlotsRunUc
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class PlotsRunUcImpl(PlotsRunUc):
    """
    Use case implementation for validating and executing benchmark plots.

    This class orchestrates the execution of all plots defined in a benchmark,
    handling validation and execution errors according to the configured mode.

    Parameters
    ----------
    error_handling_mode : UseCaseErrorHandlingMode, optional
        Determines behavior when plot validation or execution fails.
        - FAIL_ON_ERROR: Stop on first error and return Failure
        - CONTINUE_ON_ERROR: Log warning and continue with remaining plots
        Default is FAIL_ON_ERROR.

    Attributes
    ----------
    error_handling_mode : UseCaseErrorHandlingMode
        The configured error handling strategy.

    Notes
    -----
    Plot execution is sequential and order-dependent based on the benchmark
    configuration. Each plot is validated before execution.
    """

    def __init__(
        self,
        error_handling_mode: UseCaseErrorHandlingMode = UseCaseErrorHandlingMode.FAIL_ON_ERROR,
    ) -> None:
        """
        Initialize the plots run use case.

        Parameters
        ----------
        error_handling_mode : UseCaseErrorHandlingMode, optional
            Error handling strategy for plot validation and execution failures.
            Default is FAIL_ON_ERROR.
        """
        self._logger = Logging.get_logger(__name__)
        self.error_handling_mode = error_handling_mode

    def __call__(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[None, PlotRunError | UnknownLunaBenchError]:
        """
        Execute all plots defined in the benchmark.

        This method iterates through all plots in the benchmark, validates each
        plot against the benchmark data, and executes the plot generation if
        validation succeeds. Error handling behavior depends on the configured
        error_handling_mode.

        Parameters
        ----------
        benchmark : BenchmarkUserModel
            The benchmark containing plots to execute and the data (metrics,
            features, algorithms, models) required for plot generation.

        Returns
        -------
        Result[None, PlotRunError | UnknownLunaBenchError]
            Success(None) if all plots executed successfully (or if errors were
            handled gracefully in CONTINUE_ON_ERROR mode). Failure with PlotRunError
            if validation fails, or UnknownLunaBenchError if execution raises an
            exception (only in FAIL_ON_ERROR mode).

        Notes
        -----
        - In FAIL_ON_ERROR mode: Returns Failure on first validation or execution error
        - In CONTINUE_ON_ERROR mode: Logs warnings and continues with remaining plots
        - Validation is performed before execution for each plot
        - Plot execution order follows the order defined in the benchmark
        """
        for plot in benchmark.plots:
            validation_result = plot.plot.validate_plot(benchmark)
            if not is_successful(validation_result):
                if self.error_handling_mode == UseCaseErrorHandlingMode.FAIL_ON_ERROR:
                    return Failure(validation_result.failure())
                self._logger.warning(f"Plot {plot.name} validation failed with error: {validation_result.failure()}")
                continue

            try:
                plot.plot.run(**validation_result.unwrap())
            except Exception as e:
                self._logger.warning(f"Plot {plot.name} execution failed with error: {e}")
                if self.error_handling_mode == UseCaseErrorHandlingMode.FAIL_ON_ERROR:
                    return Failure(UnknownLunaBenchError(e))

        return Success(None)
