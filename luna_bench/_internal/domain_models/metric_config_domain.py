from pydantic import BaseModel, ConfigDict

from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .metric_result_domain import MetricResultDomain


class MetricConfigDomain(BaseDomain):
    class MetricConfig(BaseModel):
        model_config = ConfigDict(extra="allow")

    id: int
    name: str

    status: JobStatus
    result: MetricResultDomain | None

    config_data: MetricConfig
