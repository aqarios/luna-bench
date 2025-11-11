from typing import Any

from luna_quantum import Model, Solution, config
from luna_quantum.client.schemas.enums.status import StatusEnum
from luna_quantum.solve import SolveJob
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync

config.LUNA_LOG_DISABLE_SPINNER = True


class LunaData(BaseModel):
    luna_id: str


class LunaAlgorithm(AlgorithmAsync[LunaData], IAlgorithm[Any]):
    @property
    def model_type(self) -> type[LunaData]:
        return LunaData

    def run_async(self, model: Model) -> LunaData:
        solve_job: SolveJob = self.run(model)
        return LunaData(luna_id=solve_job.id)

    def fetch_result(self, model: Model, retrieval_data: LunaData) -> Result[Solution, str]:
        solve_job: SolveJob = SolveJob.get_by_id(retrieval_data.luna_id)
        solve_job._model = model  # noqa: SLF001 # need to access private member so luna quantum does not raise a warning
        solution: Solution | None = solve_job.result()

        if solution:
            return Success(solution)

        match solve_job.status:
            case StatusEnum.REQUESTED | StatusEnum.CREATED | StatusEnum.IN_PROGRESS:
                return Failure("The solve job has not completed yet.")
            case StatusEnum.DONE:
                return Failure("Job reported DONE but no solution was returned.")
            case StatusEnum.FAILED:
                return (
                    Failure(solve_job.error_message)
                    if solve_job.error_message
                    else Failure("Solve job failed, but there was no error message.")
                )
            case StatusEnum.CANCELED:
                return Failure("The solve job was canceled.")
            case _:
                return Failure(f"Unknown solve job status: {solve_job.status}")

    @classmethod
    def registered_id_from_algorithm(cls, algorithm: type[IAlgorithm[Any]]) -> str:
        return f"{cls.__module__}.{cls.__qualname__}[{algorithm.__qualname__}]"
