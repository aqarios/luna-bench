from luna_quantum.solve.domain.abstract import LunaAlgorithm
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus


class Job(BaseModel):
    
    name: str
    status: JobStatus
    
    backend: IBackend | None
    algorithm: LunaAlgorithm

    def run(self) -> None: ...

    def result(self) -> None: ...

    def reset(self) -> None: ...
