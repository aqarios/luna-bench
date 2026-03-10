from __future__ import annotations

from luna_bench.entities import (
    AlgorithmEntity,
    AlgorithmResultEntity,
    FeatureEntity,
    FeatureResultEntity,
    MetricEntity,
    MetricResultEntity,
)
from luna_bench.entities.enums import JobStatus
from luna_bench.types import FeatureResult, MetricResult

from .mock_components import MockAlgorithm, MockFeature, MockMetric


def make_feature_entity(
    name: str,
    *model_results: tuple[str, dict[str, object]],
) -> FeatureEntity:
    """Create a FeatureEntity with results from (model_name, {field: value}) tuples."""
    results = {}
    for model_name, fields in model_results:
        results[model_name] = FeatureResultEntity(
            processing_time_ms=10,
            model_name=model_name,
            status=JobStatus.DONE,
            error=None,
            result=FeatureResult.model_construct(**fields),  # type: ignore[arg-type]
        )
    return FeatureEntity(name=name, status=JobStatus.DONE, feature=MockFeature(), results=results)


def make_metric_entity(
    name: str,
    *algo_model_results: tuple[str, str, dict[str, object]],
    status: JobStatus = JobStatus.DONE,
    error: str | None = None,
) -> MetricEntity:
    """Create a MetricEntity with results from (algo, model, {field: value}) tuples."""
    results = {}
    for algo, model, fields in algo_model_results:
        results[(algo, model)] = MetricResultEntity(
            processing_time_ms=100,
            model_name=model,
            algorithm_name=algo,
            status=status,
            error=error,
            result=MetricResult.model_construct(**fields) if fields else None,  # type: ignore[arg-type]
        )
    return MetricEntity(name=name, status=status, metric=MockMetric(), results=results)


def make_algo_entity(name: str, model_names: list[str]) -> AlgorithmEntity:
    """Create an AlgorithmEntity with empty results for given models."""
    return AlgorithmEntity(
        name=name,
        status=JobStatus.DONE,
        algorithm=MockAlgorithm(),
        results={
            m: AlgorithmResultEntity(
                meta_data=None,
                status=JobStatus.DONE,
                error=None,
                solution=None,
                task_id=None,
                retrival_data=None,
                model_id=i,
            )
            for i, m in enumerate(model_names)
        },
    )
