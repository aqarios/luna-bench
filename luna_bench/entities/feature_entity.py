from __future__ import annotations

from pydantic import BaseModel

from luna_bench.base_components import BaseFeature
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.types import FeatureName

from .enums import JobStatus


class FeatureEntity(BaseModel):
    """Represents a fully configured feature."""

    name: FeatureName
    status: JobStatus

    feature: BaseFeature

    results: dict[FeatureName, FeatureResultEntity]  # key is the model name
