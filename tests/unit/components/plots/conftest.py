from collections.abc import Callable
from typing import Any

import numpy as np

from luna_bench.base_components.base_feature import BaseFeature
from luna_bench.base_components.base_metric import BaseMetric
from luna_bench.components.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult
from luna_bench.components.metrics.fake_metric import FakeMetric, FakeMetricResult
from luna_bench.components.plots.generics.features_plot import FeaturesValidationResult
from luna_bench.components.plots.generics.metrics_plot import MetricsValidationResult
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.entities.metric_result_entity import MetricResultEntity
from luna_bench.types import FeatureResult


def mock_metric_entity(
    *values: tuple[str, str, float],
    name: str,
    metric: BaseMetric,
    result_factory: Callable[[float], Any],
    status: JobStatus = JobStatus.DONE,
    error: str | None = None,
) -> MetricEntity:
    results = {}
    for algo, model, val in values:
        results[(algo, model)] = MetricResultEntity(
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
    feature: BaseFeature,
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


def mock_var_validation_result(*values: tuple[str, int]) -> FeaturesValidationResult:
    return FeaturesValidationResult(
        features={VarNumberFeature.registered_id: mock_var_entity(*values)},
    )


def mock_fake_metric_validation_result(
    *values: tuple[str, str],
    random_number: float | None = None,
    status: JobStatus = JobStatus.DONE,
    error: str | None = None,
) -> MetricsValidationResult:
    rand_int = int(np.random.default_rng().integers(low=0, high=100) if random_number is None else random_number)
    return MetricsValidationResult(
        metrics={
            FakeMetric.registered_id: mock_metric_entity(
                *((algo, model, rand_int) for algo, model in values),
                name="fake",
                metric=FakeMetric(),
                result_factory=lambda v: FakeMetricResult(random_number=int(v)),
                status=status,
                error=error,
            )
        }
    )
