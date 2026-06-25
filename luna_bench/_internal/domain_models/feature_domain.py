from .base_domain import BaseDomain
from .feature_result_domain import FeatureResultDomain
from .registered_data_domain import RegisteredDataDomain


class FeatureDomain(BaseDomain):
    name: str

    results: dict[str, FeatureResultDomain]  # key is the model name

    config_data: RegisteredDataDomain
