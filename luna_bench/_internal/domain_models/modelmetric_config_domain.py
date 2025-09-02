from luna_quantum.client.schemas.enums.status import StatusEnum
from pydantic import BaseModel, ConfigDict

from .base_domain import BaseDomain


class ModelmetricConfigDomain(BaseDomain):
    class ModelmetricConfig(BaseModel):
        model_config = ConfigDict(extra="allow")

    id: int
    name: str

    status: StatusEnum

    config_data: ModelmetricConfig
