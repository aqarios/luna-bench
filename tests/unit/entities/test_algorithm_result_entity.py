from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from luna_bench.entities.algorithm_result_entity import AlgorithmResultEntity
from luna_bench.entities.enums import JobStatus

if TYPE_CHECKING:
    from luna_model import Solution


@pytest.fixture()
def entity(solution: Solution) -> AlgorithmResultEntity:
    return AlgorithmResultEntity(
        meta_data=None,
        status=JobStatus.DONE,
        error=None,
        solution=solution,
        task_id="task-1",
        retrival_data=None,
        model_id=7,
    )


class TestResultDump:
    """``result_dump`` replaces the solution with its serialized form."""

    def test_serializes_the_solution(self, entity: AlgorithmResultEntity, solution: Solution) -> None:
        data = entity.result_dump()

        assert data["solution"] == solution.serialize()
        assert data["status"] == JobStatus.DONE
        assert data["model_id"] == 7

    def test_a_missing_solution_dumps_as_none(self, entity: AlgorithmResultEntity) -> None:
        entity.solution = None

        assert entity.result_dump()["solution"] is None

    def test_excluding_the_solution_omits_it_entirely(self, entity: AlgorithmResultEntity) -> None:
        data = entity.result_dump(exclude={"solution"})

        assert "solution" not in data

    def test_other_fields_can_be_excluded(self, entity: AlgorithmResultEntity, solution: Solution) -> None:
        data = entity.result_dump(exclude={"task_id"})

        assert "task_id" not in data
        assert data["solution"] == solution.serialize()
