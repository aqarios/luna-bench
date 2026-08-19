from abc import ABC
from typing import Any

from luna_model import Model, Solution
from luna_quantum.client.schemas.enums.status import StatusEnum
from luna_quantum.solve import SolveJob
from luna_quantum.solve.domain.abstract import LunaAlgorithm as LunaQuantumAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import BaseModel, field_validator, model_serializer
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from returns.result import Failure, Result, Success

from luna_bench.configs.config import config
from luna_bench.custom import BaseAlgorithmAsync

config.LB_LOG_DISABLE_SPINNER = True


class LunaData(BaseModel):
    luna_id: str | None = None
    error_message: str | None = None


class LunaAlgorithm(BaseAlgorithmAsync[LunaData], LunaQuantumAlgorithm[IBackend], ABC):
    @field_validator("backend", mode="before")
    @classmethod
    def backend_validator(cls, v: Any) -> IBackend | None:  # noqa: ANN401 # Ignore ANN401 here because the type for validation could be every type.
        if isinstance(v, dict):
            backend_class_name = v.pop("backend_class_name", None)
            backend_data = v.pop("backend_data", None)

            for b in cls.get_compatible_backends():
                if b.__name__ == backend_class_name:
                    v = b.model_construct(**backend_data)
                    break

        return super().backend_validator(v)

    @model_serializer(mode="wrap")
    def _serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)

        if self.backend is not None:
            # Pydantic serializers may modify the data_dir of the `self.backend.model_dump()` method.
            # Therfore, we use dict() to bypass any custom serializers.
            backend_data = dict(self.backend)

            backend_class_name = self.backend.__class__.__name__

            data["backend"] = {}
            data["backend"]["backend_class_name"] = backend_class_name
            data["backend"]["backend_data"] = backend_data

        return data

    @property
    def model_type(self) -> type[LunaData]:
        return LunaData

    def run_async(self, model: Model) -> LunaData:
        try:
            backend = self.backend_validator(self.backend)

            # `_serialize` re-adds `backend` to the dump so luna-bench can persist it, but
            # luna-quantum forwards that very dump to the solve API as the solver parameters,
            # where an unknown `backend` key is rejected. Running on a copy that has no backend
            # set keeps those parameters clean; the backend is handed over explicitly instead.
            runner = self.model_copy(update={"backend": None})

            # luna_quantum types its Model as luna_quantum.lm_overwrites.model.Model, which mypy
            # sees as distinct from luna_model.Model even though they are the same at runtime.
            solve_job: SolveJob = runner.run(model, backend=backend)  # type: ignore[arg-type, unused-ignore]

            return LunaData(luna_id=solve_job.id)
        except Exception as e:
            error_message = e.__str__()
            self._logger.info(f"There was an exception while running the luna algorithm: {error_message}")
            return LunaData(error_message=error_message)

    def fetch_result(self, model: Model, retrieval_data: LunaData) -> Result[Solution, str]:
        if not retrieval_data.luna_id:
            if retrieval_data.error_message:
                return Failure(retrieval_data.error_message)
            return Failure("No solve job ID was provided.")

        solve_job: SolveJob = SolveJob.get_by_id(retrieval_data.luna_id)
        # See run_async: luna_quantum's Model is a distinct type to mypy but identical at runtime.
        solve_job._model = model  # type: ignore[assignment, unused-ignore] # noqa: SLF001 # need to access private member so luna quantum does not raise a warning
        solution: Solution | None = solve_job.result()

        if solution:
            return Success(solution)

        error_message: str
        match solve_job.status:
            case StatusEnum.REQUESTED | StatusEnum.QUEUED | StatusEnum.IN_PROGRESS:
                error_message = "The solve job has not completed yet."
            case StatusEnum.DONE:
                error_message = "Job reported DONE but no solution was returned."
            case StatusEnum.FAILED:
                error_message = (
                    solve_job.error_message
                    if solve_job.error_message
                    else "Solve job failed, but there was no error message."
                )

            case StatusEnum.CANCELED:
                error_message = "The solve job was canceled."
            case _:  # pragma: no cover # Only in case of new statuses added to luna quantum
                return Failure(f"Unknown solve job status: {solve_job.status}")
        return Failure(error_message)
