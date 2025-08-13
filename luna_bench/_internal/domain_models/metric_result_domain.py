from pydantic import BaseModel

from .base_domain import BaseDomain


class MetricResultDomain(BaseDomain):
    id: int

    result_data: BaseModel
