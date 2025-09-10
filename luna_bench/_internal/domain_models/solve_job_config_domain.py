from luna_quantum.solve.domain.abstract import LunaAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import BaseModel, ConfigDict

from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .solve_job_result_domain import SolveJobResultDomain


class SolveJobConfigDomain(BaseDomain):

    id: int
    name: str

    status: JobStatus

    result: SolveJobResultDomain | None

    backend: IBackend
    algorithm: LunaAlgorithm
