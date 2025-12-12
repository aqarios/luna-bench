from abc import ABC, abstractmethod

from luna_quantum import Solution
from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain


class IMetric(BaseModel, ABC):
    @abstractmethod
    def run(self, solution: Solution) -> ArbitraryDataDomain: ...
