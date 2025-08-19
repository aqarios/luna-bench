from luna_quantum import Solution
from pydantic import BaseModel, PrivateAttr

from .base_domain import BaseDomain


class SolveJobResultDomain(BaseDomain):
    id: int

    meta_data: BaseModel
    _solution_bytes: bytes = PrivateAttr(b"")

    @property
    def solution(self) -> Solution:
        return Solution.decode(self._solution_bytes)

    @solution.setter
    def solution(self, value: bytes | Solution) -> None:
        if isinstance(value, Solution):
            self._solution_bytes = value.encode()
        elif isinstance(value, bytes | bytearray):
            # accept bytes directly
            self._solution_bytes = bytes(value)
