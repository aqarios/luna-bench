from luna_bench.entities.enums.job_status_enum import JobStatus

from .base_domain import BaseDomain
from .feature_result_domain import FeatureResultDomain
from .registered_data_domain import RegisteredDataDomain


class FeatureDomain(BaseDomain):
    name: str

    status: JobStatus
    results: dict[str, FeatureResultDomain]  # key is the model name

    config_data: RegisteredDataDomain
