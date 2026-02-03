from luna_bench.entities.enums.job_status_enum import JobStatus

from .base_domain import BaseDomain
from .registered_data_domain import RegisteredDataDomain


class PlotDomain(BaseDomain):
    name: str

    status: JobStatus

    config_data: RegisteredDataDomain
