from pydantic import BaseModel, ConfigDict

from .base_domain import BaseDomain
from .job_status_enum import JobStatus


class PlotConfigDomain(BaseDomain):
    class PlotConfig(BaseModel):
        model_config = ConfigDict(extra="allow")

    id: int
    name: str

    status: JobStatus

    config_data: PlotConfig
