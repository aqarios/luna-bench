"""Bar plot of a single metric value, declared rather than implemented."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from luna_bench.errors.components.plots.plot_metric_undeclared_error import PlotMetricUndeclaredError

from .bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer
    from luna_bench.custom.base_results.metric_result import MetricResult
    from luna_bench.custom.types import MetricClass


class MetricBarPlot(BarPlot, ABC):
    """Base of every bar plot that draws one value of one metric.

    Those plots differ in what they read and what they are called, not in what they do:
    collect one number per model and algorithm, aggregate it per algorithm, draw it. A
    subclass therefore only declares the difference - the metric comes from its
    ``@plot(...)`` decorator, :attr:`y` names the number it reads and what to call it,
    and the reference lines are fields with the subclass' defaults:

    .. code-block:: python

        @plot(Runtime)
        class RuntimePlot(MetricBarPlot):
            y: MetricDimension = MetricDimension("runtime_seconds", "Runtime (s)")
            title: str = "Runtime per Solver"

    Because they are fields rather than hard-coded arguments, every one of them can be
    changed at construction time, e.g.
    ``RuntimePlot(title="Runtime, warm start", ylim=(0, 5))``.

    See Also
    --------
    BarPlot : Colours, error bars, annotations, grouping, and the display fields.
    """

    @property
    def metric_cls(self) -> MetricClass:
        """The metric this plot reads, taken from its ``@plot(...)`` declaration.

        Returns
        -------
        MetricClass
            The first declared metric class.

        Raises
        ------
        PlotMetricUndeclaredError
            If the plot declares no metric, so there is nothing to read.
        """
        if not self.required_metrics:
            raise PlotMetricUndeclaredError(type(self).__name__)
        return self.required_metrics[0]

    def value(self, metric_result: MetricResult) -> float:
        """Return the number a single metric result contributes.

        Parameters
        ----------
        metric_result : MetricResult
            One result of :attr:`metric_cls`.

        Returns
        -------
        float
            The value plotted for this result, by default the attribute :attr:`y` names.
        """
        return self.y.of(metric_result)

    def rows(self, benchmark_results: BenchmarkResultContainer) -> list[dict[str, Any]]:
        """Return one row per model and algorithm.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data.

        Returns
        -------
        list[dict[str, Any]]
            Rows carrying the algorithm, the model, and the plotted value under
            :attr:`y`.
        """
        return [
            {"algorithm": algorithm_name, "model": model_name, self.y.column: self.value(metric_result)}
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(self.metric_cls)
        ]

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data consumed by the plot implementation.
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
        """
        self.draw(benchmark_results=benchmark_results, rows=self.rows(benchmark_results), save_dir=save_dir)
