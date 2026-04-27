import random
from logging import Logger
from time import sleep
from typing import ClassVar

from luna_model import Model, Solution, Timer
from luna_quantum import Logging

from luna_bench.base_components import BaseAlgorithmSync
from luna_bench.helpers import algorithm


@algorithm()
class FakeAlgorithm(BaseAlgorithmSync):
    """
    Fake algorithm that does nothing.

    This algorithm is used in the development process. After that it will be deleted.
    """

    time_to_sleep: float = random.uniform(0, 2.0)  # noqa: S311

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    def run(self, model: Model) -> Solution:
        """Run a fake algorithm, which will sleep for a random amount of time."""
        timer = Timer.start()

        self._logger.info(f"Running fake algorithm for model {model.name}")
        sleep(self.time_to_sleep)
        self._logger.info(f"Done with fake algorithm for model {model.name} after {self.time_to_sleep} seconds")

        return Solution.from_dict(data=dict.fromkeys(model.variables(), 1), env=model.environment, timing=timer.stop())
