from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain


class RegisteredDataDomain(BaseModel):
    registered_id: str
    data: ArbitraryDataDomain
