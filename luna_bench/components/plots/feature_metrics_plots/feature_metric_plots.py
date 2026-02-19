"""Scatter plots combining features (x-axis) with metrics (y-axis), colour-coded by algorithm."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import seaborn as sns
from matplotlib import pyplot as plt

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.components.features.var_num_feature import VarNumberFeature
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio
from luna_bench.components.metrics.runtime import Runtime
from luna_bench.components.plots.generics.features_metrics_plot import (
    FeaturesAndMetricsValidationResult,
    GenericFeaturesMetricsPlot,
)
from luna_bench.components.plots.utils.dataframe_conversion import build_scatter_dataframe
from luna_bench.components.plots.utils.resolve_result_cls import resolve_run_return_type
from luna_bench.components.plots.utils.style import PALETTE
from luna_bench.helpers.decorators import plot
from luna_bench.types import MetricResult

if TYPE_CHECKING:
    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FeatureVsMetricScatterPlot(GenericFeaturesMetricsPlot):
    """Generic scatter plot of a metric (y) versus a feature (x), colour-coded by algorithm.

    Examples
    --------
    >>> RuntimeVsVars = FeatureVsMetricScatterPlot.create(
    ...     feature=VarNumberFeature,
    ...     feature_field="var_number",
    ...     metric=Runtime,
    ...     metric_field="runtime_seconds",
    ...     xlabel="Number of Variables",
    ...     ylabel="Runtime (s)",
    ...     title="Runtime vs Model Size",
    ... )
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

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        feature: type[BaseFeature],
        feature_field: str,
        metric: type[BaseMetric],
        metric_field: str,
        xlabel: str,
        ylabel: str,
        title: str,
        feature_result_cls: type[ArbitraryDataDomain] | None = None,
        metric_result_cls: type[MetricResult] | None = None,
        hline: float | None = None,
        hline_label: str | None = None,
    ) -> type[FeatureVsMetricScatterPlot]:
        """Create and register a ``FeatureVsMetricScatterPlot`` subclass.

        Parameters
        ----------
        feature:
            The registered feature class (x-axis).
        feature_field:
            Field name on the feature's result model for the x value.
        metric:
            The registered metric class (y-axis).
        metric_field:
            Field name on the metric's result model for the y value.
        xlabel:
            Label for the x-axis.
        ylabel:
            Label for the y-axis.
        title:
            Plot title.
        feature_result_cls:
            Pydantic model for parsing feature results.
            If not provided, inferred from ``feature.run()`` return type.
        metric_result_cls:
            Pydantic model for parsing metric results.
            If not provided, inferred from ``metric.run()`` return type.
        hline:
            Optional horizontal reference line.
        hline_label:
            Legend label for the reference line.
        """
        resolved_feature_cls = feature_result_cls or resolve_run_return_type(feature, ArbitraryDataDomain)
        resolved_metric_cls = metric_result_cls or resolve_run_return_type(metric, MetricResult)
        name = f"{metric.__name__}Vs{feature.__name__}Plot"
        sub = type(
            name,
            (cls,),
            {
                "__module__": cls.__module__,
                "__qualname__": name,
                "_feature_id": feature.registered_id,
                "_feature_result_cls": resolved_feature_cls,
                "_feature_field": feature_field,
                "_metric_id": metric.registered_id,
                "_metric_result_cls": resolved_metric_cls,
                "_metric_field": metric_field,
                "_xlabel": xlabel,
                "_ylabel": ylabel,
                "_title": title,
                "_hline": hline,
                "_hline_label": hline_label,
            },
        )
        registered: type[FeatureVsMetricScatterPlot] = plot(  # type: ignore[assignment,call-arg]
            metrics_ids=(metric.registered_id,),
            features_ids=(feature.registered_id,),
        )(sub)
        return registered

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Plot metric vs feature as a scatter chart."""
        df = build_scatter_dataframe(
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


RuntimeVsVarNumberPlot = FeatureVsMetricScatterPlot.create(
    feature=VarNumberFeature,
    feature_field="var_number",
    metric=Runtime,
    metric_field="runtime_seconds",
    xlabel="Number of Variables",
    ylabel="Runtime (s)",
    title="Runtime vs Model Size",
)

FeasibilityRatioVsVarNumberPlot = FeatureVsMetricScatterPlot.create(
    feature=VarNumberFeature,
    feature_field="var_number",
    metric=FeasibilityRatio,
    metric_field="feasibility_ratio",
    xlabel="Number of Variables",
    ylabel="Feasibility Ratio",
    title="Feasibility Ratio vs Model Size",
    hline=1.0,
    hline_label="Upper Limit (1.0)",
)

ApproximationRatioVsVarNumberPlot = FeatureVsMetricScatterPlot.create(
    feature=VarNumberFeature,
    feature_field="var_number",
    metric=ApproximationRatio,
    metric_field="approximation_ratio",
    xlabel="Number of Variables",
    ylabel="Approximation Ratio",
    title="Approximation Ratio vs Model Size (1.0 = optimal)",
    hline=1.0,
    hline_label="Optimal (1.0)",
)
