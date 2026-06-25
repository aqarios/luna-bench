from .base_domain import BaseDomain
from .registered_data_domain import RegisteredDataDomain


class PlotDomain(BaseDomain):
    name: str

    config_data: RegisteredDataDomain
