from __future__ import annotations

from typing import Any

from luna_quantum import Solution
from pydantic import BaseModel, field_validator

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench.errors.validation_errors.validation_solution_error import ValidationSolutionError


class AlgorithmResultUserModel(BaseModel):
    meta_data: ArbitraryDataDomain | None
    status: JobStatus
    error: str | None

    solution: Solution | None

    # TODO(Llewellyn): maybe in a future task remove these three fields and then  # noqa: FIX002
    #  load the result directly from the database inside the retrieve usecases.
    task_id: str | None
    retrival_data: ArbitraryDataDomain | None
    model_id: int

    @field_validator("solution")
    @classmethod
    def validate_solution(cls, v: Any) -> Solution | None:  # noqa: ANN401 # we here want to be able to validate all types
        if v is None or isinstance(v, Solution):
            return v
        raise ValidationSolutionError("solution")

    class Config:
        arbitrary_types_allowed = True
