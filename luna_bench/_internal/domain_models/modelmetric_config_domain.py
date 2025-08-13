from luna_quantum.client.schemas.enums.status import StatusEnum
from pydantic import BaseModel

from .base_domain import BaseDomain


class ModelmetricConfigDomain(BaseDomain):
    id: int
    name: str

    status: StatusEnum

    config_data: BaseModel
