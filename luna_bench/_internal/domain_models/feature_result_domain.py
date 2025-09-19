from pydantic import ConfigDict

from .base_domain import BaseDomain


class FeatureResultDomain(BaseDomain):
    model_config = ConfigDict(extra="allow")
