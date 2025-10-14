from abc import ABC, abstractmethod

from pydantic import BaseModel


class IPlot(BaseModel, ABC):
    @abstractmethod
    def run(self) -> None: ...
