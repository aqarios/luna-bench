"""Scatter plots combining features (x-axis) with metrics (y-axis), colour-coded by algorithm."""

import logging
from typing import ClassVar

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


class FeatureVsMetricScatterPlot(GenericFeaturesMetricsPlot):
    """Generic scatter plot of a metric (y) versus a feature (x), colour-coded by algorithm.

    Subclasses declare the feature and metric to plot via ClassVar attributes and
    register themselves with the ``@plot`` decorator.

    Attributes
    ----------
    _feature_id : ClassVar[str]
        Registered id of the feature (x-axis).
    _feature_result_cls : ClassVar[type[BaseModel]]
        Pydantic model for parsing feature results.
    _feature_field : ClassVar[str]
        Field name on *_feature_result_cls* for the x value.
    _metric_id : ClassVar[str]
        Registered id of the metric (y-axis).
    _metric_result_cls : ClassVar[type[BaseModel]]
        Pydantic model for parsing metric results.
    _metric_field : ClassVar[str]
        Field name on *_metric_result_cls* for the y value.
    _xlabel : ClassVar[str]
        Label for the x-axis.
    _ylabel : ClassVar[str]
        Label for the y-axis.
    _title : ClassVar[str]
        Plot title.
    _hline : ClassVar[float | None]
        Optional horizontal reference line.
    _hline_label : ClassVar[str | None]
        Legend label for the reference line.

    Examples
    --------
    >>> @plot(metrics_ids=(MyMetric.registered_id,), features_ids=(MyFeature.registered_id,))
    ... class MyScatterPlot(FeatureVsMetricScatterPlot):
    ...     _feature_id = MyFeature.registered_id
    ...     _feature_result_cls = MyFeatureResult
    ...     _feature_field = "some_field"
    ...     _metric_id = MyMetric.registered_id
    ...     _metric_result_cls = MyMetricResult
    ...     _metric_field = "some_value"
    ...     _xlabel = "Some Feature"
    ...     _ylabel = "Some Metric"
    ...     _title = "Some Metric vs Some Feature"
    """

    _feature_id: ClassVar[str]
    _feature_result_cls: ClassVar[type[BaseModel]]
    _feature_field: ClassVar[str]
    _metric_id: ClassVar[str]
    _metric_result_cls: ClassVar[type[BaseModel]]
    _metric_field: ClassVar[str]
    _xlabel: ClassVar[str]
    _ylabel: ClassVar[str]
    _title: ClassVar[str]
    _hline: ClassVar[float | None] = None
    _hline_label: ClassVar[str | None] = None

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Plot metric vs feature as a scatter chart."""
        df = _build_scatter_dataframe(
            data.features[self._feature_id],
            self._feature_result_cls,
            self._feature_field,
            data.metrics[self._metric_id],
            self._metric_result_cls,
            self._metric_field,
        )
        if df.empty:
            logger.warning("%s: no data to plot", type(self).__name__)
            return

        n_algorithms = df["algorithm"].nunique()
        plt.figure(figsize=(8, 5))
        sns.scatterplot(
            data=df,
            x=self._feature_field,
            y=self._metric_field,
            hue="algorithm",
            palette=PALETTE[:n_algorithms],
            s=60,
            alpha=0.8,
        )
        if self._hline is not None:
            plt.axhline(y=self._hline, color=PALETTE[1], linestyle="--", alpha=0.7, label=self._hline_label)
        plt.xlabel(self._xlabel)
        plt.ylabel(self._ylabel)
        plt.title(self._title)
        plt.legend(title="Algorithm")
        plt.tight_layout()
        plt.show()


@plot(metrics_ids=(Runtime.registered_id,), features_ids=(VarNumberFeature.registered_id,))
class RuntimeVsVarNumberPlot(FeatureVsMetricScatterPlot):  # type: ignore[call-arg]
    """Scatter plot of runtime (y) versus number of variables (x), colour-coded by algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_num", feature=VarNumberFeature())
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="rt_vs_vars", plot=RuntimeVsVarNumberPlot())
    """

    _feature_id: ClassVar[str] = VarNumberFeature.registered_id
    _feature_result_cls: ClassVar[type[BaseModel]] = VarNumberFeatureResult
    _feature_field: ClassVar[str] = "var_number"
    _metric_id: ClassVar[str] = Runtime.registered_id
    _metric_result_cls: ClassVar[type[BaseModel]] = RuntimeResult
    _metric_field: ClassVar[str] = "runtime_seconds"
    _xlabel: ClassVar[str] = "Number of Variables"
    _ylabel: ClassVar[str] = "Runtime (s)"
    _title: ClassVar[str] = "Runtime vs Model Size"


@plot(metrics_ids=(FeasibilityRatio.registered_id,), features_ids=(VarNumberFeature.registered_id,))
class FeasibilityRatioVsVarNumberPlot(FeatureVsMetricScatterPlot):  # type: ignore[call-arg]
    """Scatter plot of feasibility ratio (y) versus number of variables (x), colour-coded by algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_num", feature=VarNumberFeature())
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="feas_vs_vars", plot=FeasibilityRatioVsVarNumberPlot())
    """

    _feature_id: ClassVar[str] = VarNumberFeature.registered_id
    _feature_result_cls: ClassVar[type[BaseModel]] = VarNumberFeatureResult
    _feature_field: ClassVar[str] = "var_number"
    _metric_id: ClassVar[str] = FeasibilityRatio.registered_id
    _metric_result_cls: ClassVar[type[BaseModel]] = FeasibilityRatioResult
    _metric_field: ClassVar[str] = "feasibility_ratio"
    _xlabel: ClassVar[str] = "Number of Variables"
    _ylabel: ClassVar[str] = "Feasibility Ratio"
    _title: ClassVar[str] = "Feasibility Ratio vs Model Size"
    _hline: ClassVar[float | None] = 1.0
    _hline_label: ClassVar[str | None] = "Upper Limit (1.0)"


@plot(metrics_ids=(ApproximationRatio.registered_id,), features_ids=(VarNumberFeature.registered_id,))
class ApproximationRatioVsVarNumberPlot(FeatureVsMetricScatterPlot):  # type: ignore[call-arg]
    """Scatter plot of approximation ratio (y) versus number of variables (x), colour-coded by algorithm.

    A value of 1.0 is optimal. Values > 1.0 indicate worse solution quality.

    Examples
    --------
    >>> bench.add_feature(name="var_num", feature=VarNumberFeature())
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="approx_vs_vars", plot=ApproximationRatioVsVarNumberPlot())
    """

    _feature_id: ClassVar[str] = VarNumberFeature.registered_id
    _feature_result_cls: ClassVar[type[BaseModel]] = VarNumberFeatureResult
    _feature_field: ClassVar[str] = "var_number"
    _metric_id: ClassVar[str] = ApproximationRatio.registered_id
    _metric_result_cls: ClassVar[type[BaseModel]] = ApproximationRatioResult
    _metric_field: ClassVar[str] = "approximation_ratio"
    _xlabel: ClassVar[str] = "Number of Variables"
    _ylabel: ClassVar[str] = "Approximation Ratio"
    _title: ClassVar[str] = "Approximation Ratio vs Model Size (1.0 = optimal)"
    _hline: ClassVar[float | None] = 1.0
    _hline_label: ClassVar[str | None] = "Optimal (1.0)"
