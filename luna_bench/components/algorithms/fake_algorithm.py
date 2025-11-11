import random
from logging import Logger
from time import sleep
from typing import ClassVar

from luna_quantum import Logging, Model, Solution

from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench.helpers import algorithm


@algorithm
class FakeAlgorithm(AlgorithmSync):
    """
    Fake algorithm that does nothing.

    This algorithm is used in the development process. After that it will be deleted.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    def run(self, model: Model) -> Solution:
        """Run a fake algorithm, which will sleep for a random amount of time."""
        self._logger.info(f"Running fake algorithm for model {model.name}")
        time_to_sleep = random.uniform(0, 2.0)  # noqa: S311
        sleep(time_to_sleep)
        self._logger.info(f"Done with fake algorithm for model {model.name} after {time_to_sleep} seconds")
        return Solution.from_dict(data=dict.fromkeys(model.variables(), time_to_sleep), env=model.environment)
