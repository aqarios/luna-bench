from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel


class FeatureUserModel(BaseModel):
    name: str
    status: JobStatus

    feature: IFeature

    results: dict[str, FeatureResultUserModel]  # key is the model name
