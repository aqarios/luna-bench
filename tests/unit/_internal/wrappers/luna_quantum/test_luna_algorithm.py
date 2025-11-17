from typing import Any
from unittest.mock import patch

import pytest
from luna_quantum import LunaSolve, Model, Solution
from luna_quantum.client.schemas.enums.status import StatusEnum
from luna_quantum.solve import SolveJob
from luna_quantum.solve.interfaces.backend_i import IBackend
from returns.pipeline import is_successful

from luna_bench._internal.wrappers.luna_quantum.algorithms import LunaAlgorithm
from luna_bench._internal.wrappers.luna_quantum.algorithms.luna_algorithm import LunaData


class FakeBackend(IBackend):
    value: int = 0

    @property
    def provider(self) -> str:
        return "fake"


class FakeLunaAlgorithm(LunaAlgorithm):
    @property
    def algorithm_name(self) -> str:
        return "fake"

    @classmethod
    def get_default_backend(cls) -> FakeBackend:
        return FakeBackend()

    @classmethod
    def get_compatible_backends(cls) -> tuple[type[IBackend], ...]:
        return (FakeBackend,)

    def run(
        self,
        model: Model | str,
        name: str | None = None,
        backend: IBackend | None = None,
        client: LunaSolve | str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> SolveJob:
        raise NotImplementedError


class FakeSolveJob:
    def __init__(self, status: StatusEnum, error_message: str | None = None, solution: Solution | None = None) -> None:
        self.id = "job_id"
        self.status = status
        self.error_message = error_message
        self.solution = solution

    def result(self) -> Solution | None:
        return self.solution


@pytest.fixture()
def demo_algorithm() -> FakeLunaAlgorithm:
    return FakeLunaAlgorithm(backend=FakeBackend())


class TestLunaAlgorithm:
    def test_run_async_success(self, demo_algorithm: FakeLunaAlgorithm, model: Model) -> None:
        class FakeSolveJob:
            id = "job_id"

        with patch.object(FakeLunaAlgorithm, "run", return_value=FakeSolveJob()):
            result = demo_algorithm.run_async(model=model)

        assert isinstance(result, LunaData)
        assert result.luna_id == "job_id"
        assert result.error_message is None

    def test_run_async_error(self, demo_algorithm: FakeLunaAlgorithm, model: Model) -> None:
        def raise_run(self: FakeLunaAlgorithm, model: Model) -> None:  # noqa: ARG001
            raise RuntimeError("an error")  # noqa: TRY003

        with patch.object(FakeLunaAlgorithm, "run", raise_run):
            result = demo_algorithm.run_async(model=model)

        assert result.luna_id is None
        assert result.error_message == "an error"

    def test_fetch_result_without_id_uses_error_message(self, demo_algorithm: FakeLunaAlgorithm, model: Model) -> None:
        r = demo_algorithm.fetch_result(model=model, retrieval_data=LunaData(luna_id=None, error_message="an error"))

        assert not is_successful(r)
        assert r.failure() == "an error"

    def test_fetch_result_without_id_and_no_error(self, demo_algorithm: FakeLunaAlgorithm, model: Model) -> None:
        r = demo_algorithm.fetch_result(model=model, retrieval_data=LunaData())

        assert not is_successful(r)
        assert r.failure() == "No solve job ID was provided."

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (StatusEnum.REQUESTED, "The solve job has not completed yet."),
            (StatusEnum.CREATED, "The solve job has not completed yet."),
            (StatusEnum.IN_PROGRESS, "The solve job has not completed yet."),
            (StatusEnum.DONE, "Job reported DONE but no solution was returned."),
            (StatusEnum.FAILED, "Solve job failed, but there was no error message."),
            (StatusEnum.CANCELED, "The solve job was canceled."),
        ],
    )
    def test_fetch_result_status_messages(
        self, demo_algorithm: FakeLunaAlgorithm, status: StatusEnum, expected: str, model: Model
    ) -> None:
        with patch.object(SolveJob, "get_by_id", classmethod(lambda cls, _id: FakeSolveJob(status))):  # noqa: ARG005
            result = demo_algorithm.fetch_result(model=model, retrieval_data=LunaData(luna_id="job_id"))

        assert not is_successful(result)
        assert result.failure() == expected

    def test_fetch_result_failed_with_error_message(self, demo_algorithm: FakeLunaAlgorithm, model: Model) -> None:
        with patch.object(
            SolveJob,
            "get_by_id",
            classmethod(lambda _, _id: FakeSolveJob(status=StatusEnum.FAILED, error_message="an error")),
        ):
            result = demo_algorithm.fetch_result(model=model, retrieval_data=LunaData(luna_id="job_id"))

        assert not is_successful(result)
        assert result.failure() == "an error"

    def test_fetch_result_success_returns_solution(
        self, demo_algorithm: FakeLunaAlgorithm, model: Model, solution: Solution
    ) -> None:
        with patch.object(
            SolveJob, "get_by_id", classmethod(lambda _, _id: FakeSolveJob(status=StatusEnum.DONE, solution=solution))
        ):
            result = demo_algorithm.fetch_result(model=model, retrieval_data=LunaData(luna_id="jid"))

        assert is_successful(result)
        assert result.unwrap() is solution

    def test_data_type(self, demo_algorithm: FakeLunaAlgorithm) -> None:
        assert demo_algorithm.model_type == LunaData

    def test_backend_round_trip_preserves_backend(self) -> None:
        demo_algorithm = FakeLunaAlgorithm(backend=FakeBackend(value=42))

        json = demo_algorithm.model_dump()
        assert json.get("backend") is not None
        assert json["backend"].get("backend_class_name") == "FakeBackend"
        assert json["backend"].get("backend_data") == {"value": 42}
        data = FakeLunaAlgorithm.model_construct(**json)
        data.backend = FakeLunaAlgorithm.backend_validator(data.backend)

        assert data.backend is not None
        assert getattr(data.backend, "value", None) == 42
        assert isinstance(data.backend, FakeBackend)
