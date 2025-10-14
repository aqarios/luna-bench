from abc import ABC, abstractmethod

from pydantic import BaseModel


class IMetric(BaseModel, ABC):
    @abstractmethod
    def run(self) -> None: ...
