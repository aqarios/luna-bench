from pydantic import BaseModel, ConfigDict


class PlotConfigDomain(BaseModel):
    id: int
    name: str

    status

    # All not listed extras will be put into the config_data json field in the db.

    model_config = ConfigDict(extra="allow")
