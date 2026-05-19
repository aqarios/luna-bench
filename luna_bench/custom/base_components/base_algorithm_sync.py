from abc import ABC, abstractmethod

from luna_model import Model, Solution

from .meta_classes.registered_class_meta import RegisteredClassMeta
from .registerable_component import RegisterableComponent


class BaseAlgorithmSync(RegisterableComponent, ABC, metaclass=RegisteredClassMeta):
    """
    Base class for synchronous algorithms.

    Synchronous algorithms are executed on in a different process than the main benchmark, but they will
    always return a result when the run method is completed.
    """

    @abstractmethod
    def run(self, model: Model) -> Solution:
        """
        Run the algorithm synchronously.

        Parameters
        ----------
        model: Model
            The model for which the algorithm should be run.

        Returns
        -------
        Solution
            The solution of the algorithm.
        """
