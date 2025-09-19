from pydantic import ConfigDict

from .base_domain import BaseDomain


class MetricResultDomain(BaseDomain):
    model_config = ConfigDict(extra="allow")
