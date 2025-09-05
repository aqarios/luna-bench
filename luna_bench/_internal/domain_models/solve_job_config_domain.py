from pydantic import BaseModel, ConfigDict

from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .solve_job_result_domain import SolveJobResultDomain


class SolveJobConfigDomain(BaseDomain):
    class SolveJobConfig(BaseModel):
        model_config = ConfigDict(extra="allow")

    id: int
    name: str

    status: JobStatus

    config_data: SolveJobConfig
    result: SolveJobResultDomain | None
