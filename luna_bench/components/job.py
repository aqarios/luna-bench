from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend


class Job:
    backend: IBackend
    algorithm: IAlgorithm

    def run(self): ...

    def result(self): ...

    def reset(self): ...
