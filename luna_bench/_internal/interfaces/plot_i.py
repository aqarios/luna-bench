from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel
from returns.result import Result

from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel


class IPlot[TValidationResult](BaseModel, ABC):
    """
    Base interface for all plot components.

    Subclasses should implement the `run` method.

    """

    @abstractmethod
    def run(self, data: TValidationResult) -> None:
        """
        Execute the plot generation logic.

        Subclasses must override this method.
        The method should generate and save the plot using the provided data.=
        """

    @abstractmethod
    def validate_plot(
        self,
        benchmark: "BenchmarkUserModel",
    ) -> Result[TValidationResult, PlotRunError | UnknownLunaBenchError]:
        """
        Validate the plot from benchmark data.

        Parameters
        ----------
        benchmark : BenchmarkUserModel
            The benchmark containing metrics, features, and other configuration.

        Returns
        -------
        Result[None, MetricsMissingError | FeaturesMissingError | UnknownLunaBenchError]
            Success if plot was generated, Failure with appropriate error otherwise.
        """
