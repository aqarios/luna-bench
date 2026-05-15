import random
from logging import Logger
from time import sleep
from typing import ClassVar

from luna_model import Model, Solution
from luna_quantum import Logging

from luna_bench.custom import BaseAlgorithmSync, algorithm


class _CustomError(Exception):
    """Custom error class."""

    def __init__(self, time: float) -> None:
        super().__init__(f"Failing algorithm failed after {time} seconds")


@algorithm
class FailingAlgorithm(BaseAlgorithmSync):
    """
    Fake algorithm that does nothing.

    This algorithm is used in the development process. After that it will be deleted.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    time_to_sleep: float = random.uniform(0, 2.0)

    def run(self, model: Model) -> Solution:
        """Run a failing algorithm, which will raise an error after a random time."""
        self._logger.info(f"Running failing algorithm for model {model.name}")
        sleep(self.time_to_sleep)
        raise _CustomError(self.time_to_sleep)


@algorithm
class FailingArbitraryErrorAlgorithm(BaseAlgorithmSync):
    """
    Fake algorithm that does nothing.

    This algorithm is used in the development process. After that it will be deleted.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    time_to_sleep: float = random.uniform(0, 0.1)

    def run(self, model: Model) -> Solution:
        """Run a failing algorithm, which will raise an error after a random time."""
        self._logger.info(f"Running failing algorithm for model {model.name}")
        sleep(self.time_to_sleep)
        msg = "This algorithm failed due to an ValueError error."
        raise ValueError(msg)
