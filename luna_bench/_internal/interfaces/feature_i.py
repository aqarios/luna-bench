from abc import ABC, abstractmethod

from luna_quantum import Model
from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain


class IFeature(BaseModel, ABC):
    @abstractmethod
    def run(self, model: Model) -> ArbitraryDataDomain: ...
