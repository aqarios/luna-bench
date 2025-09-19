from luna_quantum import Solution
from pydantic import PrivateAttr

from .arbitrary_data_domain import ArbitraryDataDomain
from .base_domain import BaseDomain


class AlgorithmResultDomain(BaseDomain):
    meta_data: ArbitraryDataDomain
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

    @property
    def solution_bytes(self) -> bytes:
        return self._solution_bytes

    @solution_bytes.setter
    def solution_bytes(self, value: bytes) -> None:
        self._solution_bytes = value
