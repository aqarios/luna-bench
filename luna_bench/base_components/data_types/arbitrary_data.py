from pydantic import BaseModel, ConfigDict


class ArbitraryData(BaseModel):
    """Pydantic model for arbitrary data.

    This model allows for any extra fields to be added to the data, making it flexible for various use cases.
    """

    model_config = ConfigDict(extra="allow")
