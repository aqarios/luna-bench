from pydantic import BaseModel

from .base_domain import BaseDomain


class ModelmetricResultDomain(BaseDomain):
    id: int

    result_data: BaseModel
