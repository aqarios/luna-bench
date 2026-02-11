"""Built-in metric plots for common benchmarking visualizations.

Each plot requires specific metrics to be added to the benchmark. The ``@plot``
decorator declares which ``metrics_ids`` a plot needs; the framework validates
their presence before calling ``run()``.
"""

import logging

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


def _plot_average_per_solver(  # noqa: PLR0913
    df: pd.DataFrame,
    value_field: str,
    ylabel: str,
    title: str,
    *,
    ylim: tuple[float, float] | None = None,
    hline: float | None = None,
    hline_label: str | None = None,
) -> None:
    """Render a bar chart of the average metric value per algorithm."""
    plt.figure(figsize=(8, 5))
    sns.barplot(data=df, x="algorithm", y=value_field, errorbar="sd", palette=PALETTE)
    if hline is not None:
        plt.axhline(y=hline, color=PALETTE[1], linestyle="--", alpha=0.7, label=hline_label)
        plt.legend()
    plt.ylabel(ylabel)
    plt.xlabel("Algorithm")
    plt.title(title)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


@plot(metrics_ids=(Runtime.registered_id,))
class AverageRuntimePlot(GenericMetricsPlot):  # type: ignore[call-arg]
    """Bar chart of the average runtime per algorithm across all models.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="avg_runtime", plot=AverageRuntimePlot())
    """

    def run(self, data: MetricsValidationResult) -> None:
        """Plot average runtime per solver as a bar chart."""
        df = _metric_to_dataframe(data.metrics[Runtime.registered_id], RuntimeResult, "runtime_seconds")
        if df.empty:
            logger.warning("AverageRuntimePlot: no data to plot")
            return
        _plot_average_per_solver(df, "runtime_seconds", ylabel="Runtime (s)", title="Average Runtime per Solver")


@plot(metrics_ids=(FeasibilityRatio.registered_id,))
class AverageFeasibilityRatioPlot(GenericMetricsPlot):  # type: ignore[call-arg]
    """Bar chart of the average feasibility ratio per algorithm across all models.

    Examples
    --------
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="avg_feasibility", plot=AverageFeasibilityRatioPlot())
    """

    def run(self, data: MetricsValidationResult) -> None:
        """Plot average feasibility ratio per solver as a bar chart."""
        df = _metric_to_dataframe(
            data.metrics[FeasibilityRatio.registered_id], FeasibilityRatioResult, "feasibility_ratio"
        )
        if df.empty:
            logger.warning("AverageFeasibilityRatioPlot: no data to plot")
            return
        _plot_average_per_solver(
            df,
            "feasibility_ratio",
            ylabel="Feasibility Ratio",
            title="Average Feasibility Ratio per Solver",
            ylim=(0, 1.15),
        )


@plot(metrics_ids=(ApproximationRatio.registered_id,))
class AverageApproximationRatioPlot(GenericMetricsPlot):  # type: ignore[call-arg]
    """Bar chart of the average approximation ratio per algorithm across all models.

    A value of 1.0 is optimal. Values > 1.0 indicate worse solution quality.

    Examples
    --------
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="avg_approx", plot=AverageApproximationRatioPlot())
    """

    def run(self, data: MetricsValidationResult) -> None:
        """Plot average approximation ratio per solver as a bar chart."""
        df = _metric_to_dataframe(
            data.metrics[ApproximationRatio.registered_id], ApproximationRatioResult, "approximation_ratio"
        )
        if df.empty:
            logger.warning("AverageApproximationRatioPlot: no data to plot")
            return
        _plot_average_per_solver(
            df,
            "approximation_ratio",
            ylabel="Approximation Ratio",
            title="Average Approximation Ratio per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
        )


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

        plt.figure(figsize=(10, 5))
        sns.barplot(data=df, x="model", y="runtime_seconds", hue="algorithm", palette=PALETTE)
        plt.ylabel("Runtime (s)")
        plt.xlabel("Model")
        plt.title("Runtime per Model by Algorithm")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()
