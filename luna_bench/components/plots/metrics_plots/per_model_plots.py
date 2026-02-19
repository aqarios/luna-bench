"""Per-model metric bar charts, grouped by algorithm."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import seaborn as sns
from matplotlib import pyplot as plt

from luna_bench.base_components import BaseMetric
from luna_bench.components.metrics.runtime import Runtime
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot, MetricsValidationResult
from luna_bench.components.plots.utils.dataframe_conversion import metric_to_dataframe
from luna_bench.components.plots.utils.resolve_result_cls import resolve_run_return_type
from luna_bench.components.plots.utils.style import PALETTE
from luna_bench.helpers.decorators import plot
from luna_bench.types import MetricResult

if TYPE_CHECKING:
    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MetricPerModelPlot(GenericMetricsPlot):
    """Grouped bar chart showing a metric per model, with one bar group per algorithm.

    Examples
    --------
    >>> RuntimePerModel = MetricPerModelPlot.create(
    ...     metric=Runtime,
    ...     value_field="runtime_seconds",
    ...     ylabel="Runtime (s)",
    ...     title="Runtime per Model by Algorithm",
    ... )
    """

    _metric_id: ClassVar[str]
    _result_cls: ClassVar[type[BaseModel]]
    _value_field: ClassVar[str]
    _ylabel: ClassVar[str]
    _title: ClassVar[str]

    @classmethod
    def create(
        cls,
        metric: type[BaseMetric],
        value_field: str,
        ylabel: str,
        title: str,
        result_cls: type[MetricResult] | None = None,
    ) -> type[MetricPerModelPlot]:
        """Create and register a ``MetricPerModelPlot`` subclass for *metric*.

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
        """
        resolved_result_cls = result_cls or resolve_run_return_type(metric, MetricResult)
        name = f"{metric.__name__}PerModelPlot"
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
            },
        )
        registered: type[MetricPerModelPlot] = plot(metrics_ids=(metric.registered_id,))(sub)  # type: ignore[assignment,call-arg]
        return registered

    def run(self, data: MetricsValidationResult) -> None:
        """Plot metric per model grouped by algorithm."""
        df = metric_to_dataframe(data.metrics[self._metric_id], self._result_cls, self._value_field)
        if df.empty:
            logger.warning("%s: no data to plot", type(self).__name__)
            return

        n_algorithms = df["algorithm"].nunique()
        plt.figure(figsize=(10, 5))
        sns.barplot(data=df, x="model", y=self._value_field, hue="algorithm", palette=PALETTE[:n_algorithms])
        plt.ylabel(self._ylabel)
        plt.xlabel("Model")
        plt.title(self._title)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()


RuntimePerModelPlot = MetricPerModelPlot.create(
    metric=Runtime,
    value_field="runtime_seconds",
    ylabel="Runtime (s)",
    title="Runtime per Model by Algorithm",
)
