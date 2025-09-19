from __future__ import annotations

from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import BaseModel

from luna_bench._internal.domain_models import AlgorithmConfigDomain, JobStatus


class Algorithm(BaseModel):
    name: str
    status: JobStatus

    backend: IBackend | None
    algorithm: IAlgorithm | BaseModel

    def run(self) -> None: ...

    def result(self) -> None: ...

    def reset(self) -> None: ...

    def _to_domain_algorithm(self) -> AlgorithmConfigDomain.Algorithm:
        return AlgorithmConfigDomain.Algorithm.model_validate(self.algorithm.model_dump())

    def _to_domain_backend(self) -> AlgorithmConfigDomain.Backend | None:
        return AlgorithmConfigDomain.Backend.model_validate(self.backend.model_dump()) if self.backend else None

    @staticmethod
    def _from_domain(modelmetric_config_domain: AlgorithmConfigDomain) -> Algorithm:
        # TODO here we need to figure out which class is the correct IAlgorithm instance

        return Algorithm(
            name=modelmetric_config_domain.name,
            status=modelmetric_config_domain.status,
            backend=modelmetric_config_domain.backend,
            algorithm=modelmetric_config_domain.algorithm,
        )

    @staticmethod
    def _update(old_modelmetric: Algorithm, new_modelmetric: AlgorithmConfigDomain) -> None:
        old_modelmetric.name = new_modelmetric.name
        old_modelmetric.status = new_modelmetric.status
        old_modelmetric.backend = new_modelmetric.backend
        old_modelmetric.algorithm = new_modelmetric.algorithm
