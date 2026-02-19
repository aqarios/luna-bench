from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from luna_bench.entities import MetricEntity
from luna_bench.entities.feature_entity import FeatureEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel


def metric_to_dataframe(metric_entity: MetricEntity, result_cls: type[BaseModel], value_field: str) -> pd.DataFrame:
    """Extract metric results into a DataFrame with columns: algorithm, model, <value_field>."""
    rows = []
    for (algorithm_name, model_name), result in metric_entity.results.items():
        if result.result is not None:
            parsed = result_cls.model_validate(result.result.model_dump())
            value = getattr(parsed, value_field)
            if value != float("inf"):
                rows.append({"algorithm": algorithm_name, "model": model_name, value_field: value})
    return pd.DataFrame(rows)


def feature_to_dataframe(
    feature_entity: FeatureEntity,
    result_cls: type[BaseModel],
    value_field: str,
    value_accessor: Callable[[Any], Any] | None = None,
) -> pd.DataFrame:
    """Extract feature results into a DataFrame with columns: model, <value_field>.

    Parameters
    ----------
    feature_entity:
        The feature entity containing per-model results.
    result_cls:
        Pydantic model used to parse individual feature results.
    value_field:
        Field name on *result_cls* that holds the numeric value.
        For simple features, this is accessed via ``getattr(parsed, value_field)``.
    value_accessor:
        Optional callable for complex (e.g. MIP enum-keyed) results.
        When provided, called as ``value_accessor(parsed)`` and *value_field*
        is only used as the DataFrame column name.
    """
    rows = []
    for model_name, result_entity in feature_entity.results.items():
        if result_entity.result is not None:
            parsed = result_cls.model_validate(result_entity.result.model_dump())
            value = value_accessor(parsed) if value_accessor is not None else getattr(parsed, value_field)
            if value != float("inf"):
                rows.append({"model": model_name, value_field: value})
    return pd.DataFrame(rows)


def build_scatter_dataframe(  # noqa: PLR0913
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
