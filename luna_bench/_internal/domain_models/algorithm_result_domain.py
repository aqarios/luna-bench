from luna_quantum import Solution

from luna_bench.entities.enums.job_status_enum import JobStatus

from .arbitrary_data_domain import ArbitraryDataDomain
from .base_domain import BaseDomain


class AlgorithmResultDomain(BaseDomain):
    meta_data: ArbitraryDataDomain | None = None
    _solution_bytes: bytes | None = None

    model_id: int

    status: JobStatus
    error: str | None

    task_id: str | None
    retrival_data: ArbitraryDataDomain | None

    @property
    def solution(self) -> Solution | None:
        if self._solution_bytes is None:
            return None
        return Solution.decode(self._solution_bytes)

    @solution.setter
    def solution(self, value: bytes | Solution | None) -> None:
        if isinstance(value, Solution):
            self._solution_bytes = value.encode()
        elif isinstance(value, bytes | bytearray):
            # accept bytes directly
            self._solution_bytes = bytes(value)
        else:
            self._solution_bytes = None

    @property
    def solution_bytes(self) -> bytes | None:
        return self._solution_bytes

    @solution_bytes.setter
    def solution_bytes(self, value: bytes) -> None:
        self._solution_bytes = value
