from __future__ import annotations

from typing import Any

from luna_model import Solution
from pydantic import BaseModel, ConfigDict

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

from .enums import JobStatus


class AlgorithmResultEntity(BaseModel):
    """Represents a result of an algorithm execution."""

    meta_data: ArbitraryDataDomain | None
    status: JobStatus
    error: str | None

    solution: Solution | None

    # TODO(Llewellyn): maybe in a future task remove these three fields and then  # noqa: FIX002
    #  load the result directly from the database inside the retrieve usecases.
    task_id: str | None
    retrival_data: ArbitraryDataDomain | None
    model_id: int

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def result_dump(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Dump result fields, using ``serialize`` for the solution."""
        exclude = exclude or set()
        data = self.model_dump(exclude={"solution", *exclude})
        data["solution"] = self.solution.serialize() if self.solution is not None else None
        return data
