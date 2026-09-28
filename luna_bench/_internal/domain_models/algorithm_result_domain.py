from typing import Any

from luna_model import Solution

from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.helpers.metadata import decode_metadata, encode_metadata

from .arbitrary_data_domain import ArbitraryDataDomain
from .base_domain import BaseDomain


class AlgorithmResultDomain(BaseDomain):
    _solution_bytes: bytes | None = None
    _metadata_bytes: bytes | None = None

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

    @property
    def metadata(self) -> dict[str, Any] | None:
        """What the algorithm reported about the run, decoded from storage."""
        return decode_metadata(self._metadata_bytes)

    @metadata.setter
    def metadata(self, value: bytes | dict[str, Any] | None) -> None:
        """Accept the metadata as a mapping or as the bytes the database holds."""
        if isinstance(value, bytes | bytearray):
            self._metadata_bytes = bytes(value)
        else:
            self._metadata_bytes = encode_metadata(value)

    @property
    def metadata_bytes(self) -> bytes | None:
        return self._metadata_bytes

    @metadata_bytes.setter
    def metadata_bytes(self, value: bytes | None) -> None:
        self._metadata_bytes = bytes(value) if value is not None else None
