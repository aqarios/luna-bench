from typing import Any

from luna_quantum import Model
from luna_quantum.solve import SolveJob
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend

from luna_bench.helpers import algorithm


@algorithm
class FakeAlgorithm(IAlgorithm[IBackend]):
    """
    Fake algorithm that does nothing.

    This algorithm is used in the development process. After that it will be deleted.
    """

    def run(  # noqa: D102
        self,
        model: Model | str,
        name: str | None = None,
        backend: IBackend | None = None,
        *args: Any | None,
        **kwargs: Any | None,
    ) -> SolveJob:
        raise NotImplementedError
