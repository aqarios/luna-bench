from abc import ABC, abstractmethod

from luna_quantum import Model, Solution
from pydantic import BaseModel


class AlgorithmSync(BaseModel, ABC):
    @abstractmethod
    def run(self, model: Model) -> Solution: ...
