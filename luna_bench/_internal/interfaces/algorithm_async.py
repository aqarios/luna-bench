from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from luna_quantum import Model, Solution
    from returns.result import Result

T_co = TypeVar("T_co", bound=BaseModel, covariant=True)


class AlgorithmAsync[T_cov](ABC, BaseModel):
    @property
    @abstractmethod
    def model_type(self) -> type[T_cov]: ...

    @abstractmethod
    def run_async(self, model: Model) -> T_cov: ...

    @abstractmethod
    def fetch_result(self, model: Model, retrieval_data: T_cov) -> Solution | str | Result[Solution, str]: ...
