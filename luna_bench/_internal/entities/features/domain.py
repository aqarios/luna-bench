from typing import Protocol

from returns.result import Result


class Feature(Protocol):
    @staticmethod
    def calculate(model) -> Result[None, str]:
        pass
