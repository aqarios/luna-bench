from __future__ import annotations

from pydantic import BaseModel

from luna_bench.custom import BaseFeature
from luna_bench.custom.types import FeatureName, ModelName
from luna_bench.entities.feature_result_entity import FeatureResultEntity

from .enums import JobStatus


class FeatureEntity(BaseModel):
    """Represents a fully configured feature."""

    name: FeatureName
    status: JobStatus

    feature: BaseFeature

    results: dict[ModelName, FeatureResultEntity]  # key is the model name
