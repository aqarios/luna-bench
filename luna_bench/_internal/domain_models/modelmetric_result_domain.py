from pydantic import ConfigDict

from .base_domain import BaseDomain


class ModelmetricResultDomain(BaseDomain):
    model_config = ConfigDict(extra="allow")
