from abc import ABC, abstractmethod

from luna_model import Model

from luna_bench.custom.types import SolveOutcome

from .meta_classes.registered_class_meta import RegisteredClassMeta
from .registerable_component import RegisterableComponent


class BaseAlgorithmSync(RegisterableComponent, ABC, metaclass=RegisteredClassMeta):
    """
    Base class for synchronous algorithms.

    Synchronous algorithms are executed on in a different process than the main benchmark, but they will
    always return a result when the run method is completed.
    """

    @abstractmethod
    def run(self, model: Model) -> SolveOutcome:
        """
        Run the algorithm synchronously.

        Parameters
        ----------
        model: Model
            The model for which the algorithm should be run.

        Returns
        -------
        SolveOutcome
            The solution of the algorithm, either on its own or as a ``(solution, metadata)``
            pair. The metadata is a mapping of whatever the solver knows about the run that the
            solution does not carry - the device it ran on, the shots it took, a provider job id.
            It is stored with the run and reaches metrics that subclass ``BaseMetadataMetric``.
            Returning the solution alone leaves the metadata of that run empty.
        """
