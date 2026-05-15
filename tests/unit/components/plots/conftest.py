from collections.abc import Callable
from typing import Any

from luna_bench.custom import BaseFeature, BaseMetric
from luna_bench.custom.base_results.feature_result import FeatureResult
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.entities.metric_result_entity import MetricResultEntity
from luna_bench.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult


def mock_metric_entity(
    *values: tuple[str, str, float],
    name: str,
    metric: BaseMetric,
    result_factory: Callable[[float], Any],
    status: JobStatus = JobStatus.DONE,
    error: str | None = None,
) -> MetricEntity:
    results: dict[str, dict[str, MetricResultEntity]] = {}
    for algo, model, val in values:
        if model not in results:
            results[model] = {}
        results[model][algo] = MetricResultEntity(
            processing_time_ms=10,
            model_name=model,
            algorithm_name=algo,
            status=status,
            error=error,
            result=result_factory(val),
        )
    return MetricEntity(name=name, status=status, metric=metric, results=results)


def mock_feature_entity(
    name: str,
    feature: BaseFeature[Any],
    *model_names: str,
    status: JobStatus = JobStatus.CREATED,
    result_factory: Callable[[str], FeatureResult | None] | None = None,
    processing_time: int = 0,
) -> FeatureEntity:
    results = {}
    for model_name in model_names:
        results[model_name] = FeatureResultEntity.model_construct(
            processing_time_ms=processing_time,
            model_name=model_name,
            status=status,
            error=None,
            result=result_factory(model_name) if result_factory is not None else None,
        )
    return FeatureEntity(name=name, status=status, feature=feature, results=results)


def mock_var_entity(*values: tuple[str, int]) -> FeatureEntity:
    var_nums = dict(values)
    return mock_feature_entity(
        "var_num",
        VarNumberFeature(),
        *var_nums.keys(),
        status=JobStatus.DONE,
        result_factory=lambda m: FeatureResult(**VarNumberFeatureResult(var_number=var_nums[m]).model_dump()),
        processing_time=10,
    )
