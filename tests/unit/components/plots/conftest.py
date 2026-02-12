from collections.abc import Callable
from typing import Any

import numpy as np

from luna_bench.base_components.base_metric import BaseMetric
from luna_bench.components.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult
from luna_bench.components.metrics.fake_metric import FakeMetricResult
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
) -> MetricEntity:
    results = {}
    for algo, model, val in values:
        results[(algo, model)] = MetricResultEntity(
            processing_time_ms=10,
            model_name=model,
            algorithm_name=algo,
            status=JobStatus.DONE,
            error=None,
            result=result_factory(val),
        )
    return MetricEntity(name=name, status=JobStatus.DONE, metric=metric, results=results)


def mock_var_entity(*values: tuple[str, int]) -> FeatureEntity:
    results = {}
    for model_name, var_num in values:
        results[model_name] = FeatureResultEntity(
            processing_time_ms=10,
            model_name=model_name,
            status=JobStatus.DONE,
            error=None,
            result=FeatureResult(**VarNumberFeatureResult(var_number=var_num).model_dump()),
        )
    return FeatureEntity(name="var_num", status=JobStatus.DONE, feature=VarNumberFeature(), results=results)


def mock_fake_metric_result(
    model_name: str,
    alg_name: str,
    random_number: float | None = None,
    status: str | None = None,
) -> MetricResultEntity:
    rand_int = np.random.default_rng().integers(low=0, high=100) if random_number is None else random_number
    if status is not None:
        if status == "failed":
            resolved_status = JobStatus.FAILED
            error = status
        else:
            raise NotImplementedError
    else:
        resolved_status = JobStatus.DONE
        error = None
    return MetricResultEntity(
        processing_time_ms=10,
        model_name=model_name,
        algorithm_name=alg_name,
        status=resolved_status,
        error=error,
        result=FakeMetricResult(random_number=rand_int),
    )
