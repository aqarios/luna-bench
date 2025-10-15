from .base_domain import BaseDomain
from .feature_result_domain import FeatureResultDomain
from .job_status_enum import JobStatus
from .registered_data_domain import RegisteredDataDomain


class FeatureDomain(BaseDomain):
    name: str

    status: JobStatus
    result: FeatureResultDomain | None

    config_data: RegisteredDataDomain
