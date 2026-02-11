"""Scatter plots combining features (x-axis) with metrics (y-axis), colour-coded by algorithm."""

import logging

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from pydantic import BaseModel

from luna_bench.components.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio, ApproximationRatioResult
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult
from luna_bench.components.plots.generics.features_metrics_plot import (
    FeaturesAndMetricsValidationResult,
    GenericFeaturesMetricsPlot,
)
from luna_bench.components.plots.style import PALETTE
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.helpers.decorators import plot

logger = logging.getLogger(__name__)


def _build_scatter_dataframe(  # noqa: PLR0913
    feature_entity: FeatureEntity,
    feature_result_cls: type[BaseModel],
    feature_field: str,
    metric_entity: MetricEntity,
    metric_result_cls: type[BaseModel],
    metric_field: str,
) -> pd.DataFrame:
    """Build a DataFrame with columns: algorithm, model, <feature_field>, <metric_field>."""
    feature_by_model: dict[str, float] = {}
    for model_name, feat_result in feature_entity.results.items():
        if feat_result.result is not None:
            parsed = feature_result_cls.model_validate(feat_result.result.model_dump())
            feature_by_model[model_name] = getattr(parsed, feature_field)

    rows = []
    for (algorithm_name, model_name), met_result in metric_entity.results.items():
        if met_result.result is not None and model_name in feature_by_model:
            parsed = metric_result_cls.model_validate(met_result.result.model_dump())
            metric_value = getattr(parsed, metric_field)
            if metric_value != float("inf"):
                rows.append(
                    {
                        "algorithm": algorithm_name,
                        "model": model_name,
                        feature_field: feature_by_model[model_name],
                        metric_field: metric_value,
                    }
                )

    return pd.DataFrame(rows)


def _plot_scatter(  # noqa: PLR0913
    df: pd.DataFrame,
    x_field: str,
    y_field: str,
    xlabel: str,
    ylabel: str,
    title: str,
) -> None:
    """Render a scatter plot with points coloured by algorithm."""
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x=x_field, y=y_field, hue="algorithm", palette=PALETTE, s=60, alpha=0.8)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(title="Algorithm")
    plt.tight_layout()
    plt.show()


@plot(metrics_ids=(Runtime.registered_id,), features_ids=(VarNumberFeature.registered_id,))
class RuntimeVsVarNumberPlot(GenericFeaturesMetricsPlot):  # type: ignore[call-arg]
    """Scatter plot of runtime (y) versus number of variables (x), colour-coded by algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_num", feature=VarNumberFeature())
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="rt_vs_vars", plot=RuntimeVsVarNumberPlot())
    """

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Plot runtime vs number of variables."""
        df = _build_scatter_dataframe(
            data.features[VarNumberFeature.registered_id],
            VarNumberFeatureResult,
            "var_number",
            data.metrics[Runtime.registered_id],
            RuntimeResult,
            "runtime_seconds",
        )
        if df.empty:
            logger.warning("RuntimeVsVarNumberPlot: no data to plot")
            return
        _plot_scatter(
            df, "var_number", "runtime_seconds", "Number of Variables", "Runtime (s)", "Runtime vs Model Size"
        )


@plot(metrics_ids=(FeasibilityRatio.registered_id,), features_ids=(VarNumberFeature.registered_id,))
class FeasibilityRatioVsVarNumberPlot(GenericFeaturesMetricsPlot):  # type: ignore[call-arg]
    """Scatter plot of feasibility ratio (y) versus number of variables (x), colour-coded by algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_num", feature=VarNumberFeature())
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="feas_vs_vars", plot=FeasibilityRatioVsVarNumberPlot())
    """

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Plot feasibility ratio vs number of variables."""
        df = _build_scatter_dataframe(
            data.features[VarNumberFeature.registered_id],
            VarNumberFeatureResult,
            "var_number",
            data.metrics[FeasibilityRatio.registered_id],
            FeasibilityRatioResult,
            "feasibility_ratio",
        )
        if df.empty:
            logger.warning("FeasibilityRatioVsVarNumberPlot: no data to plot")
            return
        _plot_scatter(
            df,
            "var_number",
            "feasibility_ratio",
            "Number of Variables",
            "Feasibility Ratio",
            "Feasibility Ratio vs Model Size",
        )


@plot(metrics_ids=(ApproximationRatio.registered_id,), features_ids=(VarNumberFeature.registered_id,))
class ApproximationRatioVsVarNumberPlot(GenericFeaturesMetricsPlot):  # type: ignore[call-arg]
    """Scatter plot of approximation ratio (y) versus number of variables (x), colour-coded by algorithm.

    A value of 1.0 is optimal. Values > 1.0 indicate worse solution quality.

    Examples
    --------
    >>> bench.add_feature(name="var_num", feature=VarNumberFeature())
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="approx_vs_vars", plot=ApproximationRatioVsVarNumberPlot())
    """

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Plot approximation ratio vs number of variables."""
        df = _build_scatter_dataframe(
            data.features[VarNumberFeature.registered_id],
            VarNumberFeatureResult,
            "var_number",
            data.metrics[ApproximationRatio.registered_id],
            ApproximationRatioResult,
            "approximation_ratio",
        )
        if df.empty:
            logger.warning("ApproximationRatioVsVarNumberPlot: no data to plot")
            return
        _plot_scatter(
            df,
            "var_number",
            "approximation_ratio",
            "Number of Variables",
            "Approximation Ratio",
            "Approximation Ratio vs Model Size (1.0 = optimal)",
        )
