from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .registered_data_domain import RegisteredDataDomain


class PlotDomain(BaseDomain):
    name: str

    status: JobStatus

    config_data: RegisteredDataDomain
