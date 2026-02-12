"""Built-in feature bar chart plots.

Each plot requires specific features to be added to the benchmark. The ``@plot``
decorator declares which ``features_ids`` a plot needs; the framework validates
their presence before calling ``run()``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

import seaborn as sns
from matplotlib import pyplot as plt

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseFeature
from luna_bench.components.features.var_num_feature import VarNumberFeature
from luna_bench.components.plots.generics.features_plot import FeaturesValidationResult, GenericFeaturesPlot
from luna_bench.components.plots.utils.aggregation_enum import Aggregation
from luna_bench.components.plots.utils.dataframe_conversion import feature_to_dataframe
from luna_bench.components.plots.utils.resolve_result_cls import resolve_run_return_type
from luna_bench.components.plots.utils.style import PALETTE
from luna_bench.helpers.decorators import plot

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FeatureBarChartPlot(GenericFeaturesPlot):
    """Generic bar chart of a single feature value per model.

    For simple features (flat result with scalar fields), set *value_field*
    to the attribute name.

    For MIP features that use ``EnumFeatureResult`` with key-based access,
    provide a *value_accessor* callable that extracts the numeric value from
    the parsed result object.

    Examples
    --------
    Simple feature:

    >>> VarNumberBarChart = FeatureBarChartPlot.create(
    ...     feature=VarNumberFeature,
    ...     value_field="var_number",
    ...     ylabel="Number of Variables",
    ...     title="Variables per Model",
    ... )

    MIP enum-keyed feature:

    >>> BooleanVarCountPlot = FeatureBarChartPlot.create(
    ...     feature=ProblemSizeFeatures,
    ...     value_field="boolean_var_count",
    ...     ylabel="Boolean Variable Count",
    ...     title="Boolean Variables per Model",
    ...     value_accessor=lambda r: r.var_counts.get(VarTypeKey(var_type=VarType.BOOLEAN)).count,
    ... )
    """

    _feature_id: ClassVar[str]
    _result_cls: ClassVar[type[BaseModel]]
    _value_field: ClassVar[str]
    _ylabel: ClassVar[str]
    _title: ClassVar[str]
    _value_accessor: ClassVar[Callable[[Any], Any] | None] = None
    _aggregation: ClassVar[Aggregation] = Aggregation.MEAN_SD
    _ylim: ClassVar[tuple[float, float] | None] = None

    @classmethod
    def _resolve_result_cls(cls, feature: type[BaseFeature]) -> type[ArbitraryDataDomain]:
        return resolve_run_return_type(feature, ArbitraryDataDomain)

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        feature: type[BaseFeature],
        value_field: str,
        ylabel: str,
        title: str,
        result_cls: type[ArbitraryDataDomain] | None = None,
        value_accessor: Callable[[Any], Any] | None = None,
        aggregation: Aggregation = Aggregation.MEAN_SD,
        ylim: tuple[float, float] | None = None,
    ) -> type[FeatureBarChartPlot]:
        """Create and register a ``FeatureBarChartPlot`` subclass for *feature*.

        Parameters
        ----------
        feature:
            The registered feature class to plot.
        value_field:
            Field name on the feature's result model that holds the numeric
            value.  For enum-keyed results where *value_accessor* is provided,
            this is used only as the DataFrame column name.
        ylabel:
            Label for the y-axis.
        title:
            Plot title.
        result_cls:
            Pydantic model used to parse individual feature results.
            If not provided, inferred from the return type of ``feature.run``.
        value_accessor:
            Optional callable for MIP enum-keyed features.  Receives the
            parsed result object and must return a numeric value.
        aggregation:
            Aggregation strategy. Defaults to ``Aggregation.MEAN_SD``.
        ylim:
            Optional fixed y-axis limits.
        """
        resolved_result_cls = result_cls or cls._resolve_result_cls(feature)
        name = f"{feature.__name__}BarChartPlot"
        sub = type(
            name,
            (cls,),
            {
                "__module__": cls.__module__,
                "__qualname__": name,
                "_feature_id": feature.registered_id,
                "_result_cls": resolved_result_cls,
                "_value_field": value_field,
                "_ylabel": ylabel,
                "_title": title,
                "_value_accessor": value_accessor,
                "_aggregation": aggregation,
                "_ylim": ylim,
            },
        )
        registered: type[FeatureBarChartPlot] = plot(features_ids=(feature.registered_id,))(sub)  # type: ignore[assignment,call-arg]
        return registered

    def run(self, data: FeaturesValidationResult) -> None:
        """Plot feature value per model as a bar chart."""
        df = feature_to_dataframe(
            data.features[self._feature_id],
            self._result_cls,
            self._value_field,
            value_accessor=self._value_accessor,  # type: ignore[arg-type]
        )
        if df.empty:
            logger.warning("%s: no data to plot", type(self).__name__)
            return

        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=df,
            x="model",
            y=self._value_field,
            estimator=self._aggregation.estimator,
            errorbar=self._aggregation.errorbar,
            color=PALETTE[0],
            legend=False,
        )
        plt.ylabel(self._ylabel)
        plt.xlabel("Model")
        plt.title(self._title)
        if self._ylim is not None:
            plt.ylim(*self._ylim)
        plt.tight_layout()
        plt.show()


VarNumberBarChartPlot = FeatureBarChartPlot.create(
    feature=VarNumberFeature,
    value_field="var_number",
    ylabel="Number of Variables",
    title="Variables per Model",
    aggregation=Aggregation.MEAN,
)
