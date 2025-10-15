from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.interfaces.feature_i import IFeature


class FeatureUserModel(BaseModel):
    name: str
    status: JobStatus

    feature: IFeature
