"""Built-in metric plots for common benchmarking visualizations.

Each plot requires specific metrics to be added to the benchmark. The ``@plot``
decorator declares which ``metrics_ids`` a plot needs; the framework validates
their presence before calling ``run()``.
"""

import logging
from typing import ClassVar

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from pydantic import BaseModel

from luna_bench.components.metrics.approximation_ratio import ApproximationRatio, ApproximationRatioResult
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot, MetricsValidationResult
from luna_bench.components.plots.style import PALETTE
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.helpers.decorators import plot

logger = logging.getLogger(__name__)


def _metric_to_dataframe(metric_entity: MetricEntity, result_cls: type[BaseModel], value_field: str) -> pd.DataFrame:
    """Extract metric results into a DataFrame with columns: algorithm, model, <value_field>."""
    rows = []
    for (algorithm_name, model_name), result in metric_entity.results.items():
        if result.result is not None:
            parsed = result_cls.model_validate(result.result.model_dump())
            value = getattr(parsed, value_field)
            if value != float("inf"):
                rows.append({"algorithm": algorithm_name, "model": model_name, value_field: value})
    return pd.DataFrame(rows)


class AverageMetricPlot(GenericMetricsPlot):
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
    >>> @plot(metrics_ids=(MyMetric.registered_id,))
    ... class AverageMyMetricPlot(AverageMetricPlot):
    ...     _metric_id = MyMetric.registered_id
    ...     _result_cls = MyMetricResult
    ...     _value_field = "score"
    ...     _ylabel = "Score"
    ...     _title = "Average Score per Solver"
    """

    _metric_id: ClassVar[str]
    _result_cls: ClassVar[type[BaseModel]]
    _value_field: ClassVar[str]
    _ylabel: ClassVar[str]
    _title: ClassVar[str]
    _ylim: ClassVar[tuple[float, float] | None] = None
    _hline: ClassVar[float | None] = None
    _hline_label: ClassVar[str | None] = None

    def run(self, data: MetricsValidationResult) -> None:
        """Plot average metric per solver as a bar chart."""
        df = _metric_to_dataframe(data.metrics[self._metric_id], self._result_cls, self._value_field)
        if df.empty:
            logger.warning("%s: no data to plot", type(self).__name__)
            return

        n_algorithms = df["algorithm"].nunique()
        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=df,
            x="algorithm",
            y=self._value_field,
            hue="algorithm",
            errorbar="sd",
            palette=PALETTE[:n_algorithms],
            legend=False,
        )
        if self._hline is not None:
            plt.axhline(y=self._hline, color=PALETTE[1], linestyle="--", alpha=0.7, label=self._hline_label)
            plt.legend()
        plt.ylabel(self._ylabel)
        plt.xlabel("Algorithm")
        plt.title(self._title)
        if self._ylim is not None:
            plt.ylim(*self._ylim)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()


@plot(metrics_ids=(Runtime.registered_id,))
class AverageRuntimePlot(AverageMetricPlot):  # type: ignore[call-arg]
    """Bar chart of the average runtime per algorithm across all models.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="avg_runtime", plot=AverageRuntimePlot())
    """

    _metric_id: ClassVar[str] = Runtime.registered_id
    _result_cls: ClassVar[type[BaseModel]] = RuntimeResult
    _value_field: ClassVar[str] = "runtime_seconds"
    _ylabel: ClassVar[str] = "Runtime (s)"
    _title: ClassVar[str] = "Average Runtime per Solver"


@plot(metrics_ids=(FeasibilityRatio.registered_id,))
class AverageFeasibilityRatioPlot(AverageMetricPlot):  # type: ignore[call-arg]
    """Bar chart of the average feasibility ratio per algorithm across all models.

    Examples
    --------
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="avg_feasibility", plot=AverageFeasibilityRatioPlot())
    """

    _metric_id: ClassVar[str] = FeasibilityRatio.registered_id
    _result_cls: ClassVar[type[BaseModel]] = FeasibilityRatioResult
    _value_field: ClassVar[str] = "feasibility_ratio"
    _ylabel: ClassVar[str] = "Feasibility Ratio"
    _title: ClassVar[str] = "Average Feasibility Ratio per Solver"
    _ylim: ClassVar[tuple[float, float] | None] = (0, 1.15)
    _hline: ClassVar[float | None] = 1.0
    _hline_label: ClassVar[str | None] = "Upper Limit (1.0)"


@plot(metrics_ids=(ApproximationRatio.registered_id,))
class AverageApproximationRatioPlot(AverageMetricPlot):  # type: ignore[call-arg]
    """Bar chart of the average approximation ratio per algorithm across all models.

    A value of 1.0 is optimal. Values > 1.0 indicate worse solution quality.

    Examples
    --------
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="avg_approx", plot=AverageApproximationRatioPlot())
    """

    _metric_id: ClassVar[str] = ApproximationRatio.registered_id
    _result_cls: ClassVar[type[BaseModel]] = ApproximationRatioResult
    _value_field: ClassVar[str] = "approximation_ratio"
    _ylabel: ClassVar[str] = "Approximation Ratio"
    _title: ClassVar[str] = "Average Approximation Ratio per Solver (1.0 = optimal)"
    _hline: ClassVar[float | None] = 1.0
    _hline_label: ClassVar[str | None] = "Optimal (1.0)"


@plot(metrics_ids=(Runtime.registered_id,))
class RuntimePerModelPlot(GenericMetricsPlot):  # type: ignore[call-arg]
    """Grouped bar chart showing runtime per model, with one bar group per algorithm.

    Useful for comparing how solvers scale with model complexity.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="runtime_per_model", plot=RuntimePerModelPlot())
    """

    def run(self, data: MetricsValidationResult) -> None:
        """Plot runtime per model grouped by algorithm."""
        df = _metric_to_dataframe(data.metrics[Runtime.registered_id], RuntimeResult, "runtime_seconds")
        if df.empty:
            logger.warning("RuntimePerModelPlot: no data to plot")
            return

        n_algorithms = df["algorithm"].nunique()
        plt.figure(figsize=(10, 5))
        sns.barplot(data=df, x="model", y="runtime_seconds", hue="algorithm", palette=PALETTE[:n_algorithms])
        plt.ylabel("Runtime (s)")
        plt.xlabel("Model")
        plt.title("Runtime per Model by Algorithm")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()
