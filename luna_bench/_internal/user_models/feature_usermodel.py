from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel
from luna_bench.base_components import BaseFeature
from luna_bench.types import FeatureName


class FeatureUserModel(BaseModel):
    name: FeatureName
    status: JobStatus

    feature: BaseFeature

    results: dict[FeatureName, FeatureResultUserModel]  # key is the model name
