from pydantic import BaseModel

from .base_domain import BaseDomain
from .job_status_enum import JobStatus


class MetricConfigDomain(BaseDomain):
    id: int
    name: str

    status: JobStatus

    config_data: BaseModel
