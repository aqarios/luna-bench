from pydantic import BaseModel, ConfigDict


class BaseDomain(BaseModel):
    model_config = ConfigDict(extra="forbid")
