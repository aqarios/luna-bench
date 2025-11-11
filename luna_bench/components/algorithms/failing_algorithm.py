import random
from logging import Logger
from time import sleep
from typing import ClassVar

from luna_quantum import Logging, Model, Solution

from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench.helpers import algorithm


@algorithm
class FailingAlgorithm(AlgorithmSync):
    """
    Fake algorithm that does nothing.

    This algorithm is used in the development process. After that it will be deleted.
    """

    class CustomError(Exception):
        """Custom error class."""

        def __init__(self, time: float) -> None:
            super().__init__(f"Failing algorithm failed after {time} seconds")

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    def run(self, model: Model) -> Solution:
        """Run a failing algorithm, which will raise an error after a random time."""
        self._logger.info(f"Running failing algorithm for model {model.name}")
        time_to_sleep = random.uniform(0, 2.0)  # noqa: S311
        sleep(time_to_sleep)
        raise FailingAlgorithm.CustomError(time_to_sleep)
