from pydantic import BaseModel, ConfigDict


class ArbitraryDataDomain(BaseModel):
    model_config = ConfigDict(extra="allow")
