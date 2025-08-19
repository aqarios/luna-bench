from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend


class Job:
    backend: IBackend
    algorithm: IAlgorithm

    def run(self) -> None: ...

    def result(self) -> None: ...

    def reset(self) -> None: ...
