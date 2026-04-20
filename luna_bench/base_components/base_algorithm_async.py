from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeVar

from pydantic import BaseModel

from luna_bench.base_components.meta_classes.registered_class_meta import RegisteredClassMeta

if TYPE_CHECKING:
    from luna_model import Model, Solution
    from returns.result import Result

T_co = TypeVar("T_co", bound=BaseModel, covariant=True)


class BaseAlgorithmAsync[T_co](ABC, BaseModel, metaclass=RegisteredClassMeta):
    """
    Base class for all asynchronous algorithms.

    An asynchronous algorithm is one where the computation is triggered onetime, and the result is fetched at a
    later point in time. As an example, a luna quantum algorithm is onetime published to the luna cloud. The luna
    cloud will execute that algorithm while luna bench can do other stuff. At a later point in time, luna bench will
    fetch the result from the luna cloud.
    """

    registered_id: ClassVar[str]

    @property
    @abstractmethod
    def model_type(self) -> type[T_co]:
        """The data type which will be required to fetch the result of the algorithm."""

    @abstractmethod
    def run_async(self, model: Model) -> T_co:
        """
        Run the algorithm asynchronously.

        This function does not calculate a solution for the model. It triggers the calculation somewhere else.
        If there is data needed to fetch the result later, this data is returned here, so luna bench can fetch the
        solution later.

        Parameters
        ----------
        model: Model
            The model for which the algorithm should be run.

        Returns
        -------
        T_co
            The data which is needed to fetch the result of the algorithm.

        """

    @abstractmethod
    def fetch_result(self, model: Model, retrieval_data: T_co) -> Result[Solution, str]:
        """
        Fetch the result of the algorithm.

        Parameters
        ----------
        model: Model
            The model for which the result should be fetched.
        retrieval_data: T_co
            The data with which the result should be fetched.

        Returns
        -------
        Result[Solution, str]
            The result of the algorithm. if it fails, an error message is returned.

        """
