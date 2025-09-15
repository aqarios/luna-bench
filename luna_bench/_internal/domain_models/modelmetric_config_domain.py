from pydantic import BaseModel, ConfigDict

from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .modelmetric_result_domain import ModelmetricResultDomain


class ModelmetricConfigDomain(BaseDomain):
    class ModelmetricConfig(BaseModel):
        model_config = ConfigDict(extra="allow")

    id: int
    name: str

    status: JobStatus
    result: ModelmetricResultDomain | None

    config_data: ModelmetricConfig
