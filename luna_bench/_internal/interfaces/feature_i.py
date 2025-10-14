from abc import ABC, abstractmethod

from pydantic import BaseModel


class IFeature(BaseModel, ABC):
    @abstractmethod
    def run(self) -> None: ...
