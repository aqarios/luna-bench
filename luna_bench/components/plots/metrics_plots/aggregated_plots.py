"""Built-in metric plots for common benchmarking visualizations.

Each plot requires specific metrics to be added to the benchmark. The ``@plot``
decorator declares which ``metrics_ids`` a plot needs; the framework validates
their presence before calling ``run()``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from luna_bench.base_components import BaseMetric
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio
from luna_bench.components.metrics.best_solution_found import BestSolutionFound
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio
from luna_bench.components.metrics.fraction_of_overall_best_solution import FractionOfOverallBestSolution
from luna_bench.components.metrics.runtime import Runtime
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot, MetricsValidationResult
from luna_bench.components.plots.utils.aggregation_enum import Aggregation
from luna_bench.components.plots.utils.dataframe_conversion import metric_to_dataframe
from luna_bench.components.plots.utils.resolve_result_cls import resolve_run_return_type
from luna_bench.components.plots.utils.style import PALETTE
from luna_bench.helpers.decorators import plot
from luna_bench.types import MetricResult

if TYPE_CHECKING:
    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AggregatedMetricPlot(GenericMetricsPlot):
    """Generic bar chart of the average metric value per algorithm.

    Subclasses declare the metric to plot via ClassVar attributes and
    register themselves with the ``@plot`` decorator.

    Attributes
    ----------
    _metric_id : ClassVar[str]
        Registered id of the metric to plot.
    _result_cls : ClassVar[type[BaseModel]]
        Pydantic model used to parse individual metric results.
    _value_field : ClassVar[str]
        Field name on *_result_cls* that holds the numeric value.
    _ylabel : ClassVar[str]
        Label for the y-axis.
    _title : ClassVar[str]
        Plot title.
    _ylim : ClassVar[tuple[float, float] | None]
        Optional fixed y-axis limits.
    _hline : ClassVar[float | None]
        Optional horizontal reference line.
    _hline_label : ClassVar[str | None]
        Legend label for the reference line.

    Examples
    --------
    >>> AverageMyMetricPlot = AggregatedMetricPlot.create(
    ...     metric=MyMetric,
    ...     value_field="score",
    ...     ylabel="Score",
    ...     title="Average Score per Solver",
    ... )
    """

    _metric_id: ClassVar[str]
    _result_cls: ClassVar[type[BaseModel]]
    _value_field: ClassVar[str]
    _ylabel: ClassVar[str]
    _title: ClassVar[str]
    _aggregation: ClassVar[Aggregation] = Aggregation.MEAN_SD
    _ylim: ClassVar[tuple[float, float] | None] = None
    _hline: ClassVar[float | None] = None
    _hline_label: ClassVar[str | None] = None

    @classmethod
    def _resolve_result_cls(cls, metric: type[BaseMetric]) -> type[MetricResult]:
        return resolve_run_return_type(metric, MetricResult)

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        metric: type[BaseMetric],
        value_field: str,
        ylabel: str,
        title: str,
        result_cls: type[MetricResult] | None = None,
        aggregation: Aggregation = Aggregation.MEAN_SD,
        ylim: tuple[float, float] | None = None,
        hline: float | None = None,
        hline_label: str | None = None,
    ) -> type[AggregatedMetricPlot]:
        """Create and register an ``AverageMetricPlot`` subclass for *metric*.

        Parameters
        ----------
        metric:
            The registered metric class to plot.
        value_field:
            Field name on the metric's result model that holds the numeric value.
        ylabel:
            Label for the y-axis.
        title:
            Plot title.
        result_cls:
            Pydantic model used to parse individual metric results.
            If not provided, inferred from the return type of ``metric.run``.
        aggregation:
            Aggregation strategy. Defaults to ``Aggregation.MEAN_SD``.
        ylim:
            Optional fixed y-axis limits.
        hline:
            Optional horizontal reference line.
        hline_label:
            Legend label for the reference line.
        """
        resolved_result_cls = result_cls or cls._resolve_result_cls(metric)
        name = f"Average{metric.__name__}Plot"
        sub = type(
            name,
            (cls,),
            {
                "__module__": cls.__module__,
                "__qualname__": name,
                "_metric_id": metric.registered_id,
                "_result_cls": resolved_result_cls,
                "_value_field": value_field,
                "_ylabel": ylabel,
                "_title": title,
                "_aggregation": aggregation,
                "_ylim": ylim,
                "_hline": hline,
                "_hline_label": hline_label,
            },
        )
        registered: type[AggregatedMetricPlot] = plot(metrics_ids=(metric.registered_id,))(sub)  # type: ignore[assignment,call-arg]
        return registered

    def run(self, data: MetricsValidationResult) -> None:
        """Plot average metric per solver as a bar chart."""
        df = metric_to_dataframe(data.metrics[self._metric_id], self._result_cls, self._value_field)
        if df.empty:
            logger.warning("%s: no data to plot", type(self).__name__)
            return

        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=df,
            x="algorithm",
            y=self._value_field,
            estimator=self._aggregation.estimator,
            errorbar=self._aggregation.errorbar,
            color=PALETTE[0],
            legend=False,
        )
        if self._hline is not None:
            plt.axhline(y=self._hline, color=PALETTE[1], linestyle="--", alpha=0.7, label=self._hline_label)

        handles, labels = plt.gca().get_legend_handles_labels()
        if self._aggregation == Aggregation.MEAN_SD:
            err_handle = Line2D([], [], color="black", marker="|", markersize=8, linestyle="none", label="± 1 SD")
            handles.append(err_handle)
            labels.append("± 1 SD")
        if handles:
            plt.legend(handles=handles, labels=labels)

        plt.ylabel(self._ylabel)
        plt.xlabel("Algorithm")
        plt.title(self._title)
        if self._ylim is not None:
            plt.ylim(*self._ylim)
        plt.tight_layout()
        plt.show()


AverageRuntimePlot = AggregatedMetricPlot.create(
    metric=Runtime,
    value_field="runtime_seconds",
    ylabel="Runtime (s)",
    title="Average Runtime per Solver",
    aggregation=Aggregation.MEAN_SD,
)

AverageFeasibilityRatioPlot = AggregatedMetricPlot.create(
    metric=FeasibilityRatio,
    value_field="feasibility_ratio",
    ylabel="Feasibility Ratio",
    title="Average Feasibility Ratio per Solver",
    aggregation=Aggregation.MEAN_SD,
    ylim=(0, 1.15),
    hline=1.0,
    hline_label="Upper Limit (1.0)",
)

AverageApproximationRatioPlot = AggregatedMetricPlot.create(
    metric=ApproximationRatio,
    value_field="approximation_ratio",
    ylabel="Approximation Ratio",
    title="Average Approximation Ratio per Solver (1.0 = optimal)",
    aggregation=Aggregation.MEAN_SD,
    hline=1.0,
    hline_label="Optimal (1.0)",
)
AverageFoBRatioPlot = AggregatedMetricPlot.create(
    metric=FractionOfOverallBestSolution,
    value_field="fraction_of_overall_best",
    ylabel="Fraction of overall best solution",
    title="Average Fraction of overall best Ratio per Solver (1.0 = optimal)",
    aggregation=Aggregation.MEAN_SD,
    hline=1.0,
    hline_label="Optimal (1.0)",
)
AverageBestSolutionFoundRatioPlot = AggregatedMetricPlot.create(
    metric=BestSolutionFound,
    value_field="best_solution_found",
    ylabel="Best Solution Found",
    title="Average best solution found per Solver (1.0 = optimal)",
    aggregation=Aggregation.MEAN_SD,
    hline=1.0,
    hline_label="Optimal (1.0)",
)
