import tempfile
from logging import Logger
from pathlib import Path
from typing import ClassVar

from luna_quantum import Logging, Model, Solution, Timer
from luna_quantum.translator import LpTranslator, ZibTranslator
from pyscipopt import Model as PyScipModel

from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench.helpers import algorithm


class InfeasibleModelError(Exception):
    """
    Exception raised when a model solved by SCIP is identified as infeasible.

    This indicates that no feasible solution exists for the given constraints
    and cannot be used to calculate metrics in subsequent calls.
    """

    def __init__(self) -> None:
        msg = "Model is infeasible. No solution possible. Cannot be used to calculate metrics in subsequent calls."
        super().__init__(msg)


@algorithm()
class ScipAlgorithm(AlgorithmSync):
    """
    Classical exact optimization algorithm using SCIP (Solving Constraint Integer Programs).

    This algorithm wraps the SCIP solver to provide exact solutions for optimization
    problems using classical branch-and-bound methods. It translates Luna quantum models
    to LP format, solves them with SCIP, and translates the results back.

    Attributes
    ----------
        _logger: Class-level logger for tracking algorithm execution.

    Raises
    ------
        InfeasibleModelError: If the model has no feasible solution.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    def run(self, model: Model) -> Solution:
        """
        Solve an optimization model using the SCIP classical solver.

        The method performs the following steps:
        1. Translates the Luna model to LP format in a temporary file
        2. Loads the LP file into SCIP
        3. Runs SCIP's branch-and-bound optimization
        4. Translates the SCIP solution back to Luna format
        5. Returns the solution with timing information

        Args:
            model: The Luna optimization model to solve.

        Returns
        -------
            Solution object containing the optimal variable assignments,
            objective value, and timing information.

        Raises
        ------
            InfeasibleModelError: If SCIP determines the model is infeasible.

        Example:
            >>> scip_algo = ScipAlgorithm()
            >>> solution = scip_algo.run(my_model)
            >>> print(f"Objective: {solution.objective_value}")
        """
        timer = Timer.start()

        self._logger.info(f"Running SCIP for model {model.name}")
        scip_model = PyScipModel()

        # Create temporary LP file for SCIP
        with tempfile.NamedTemporaryFile(suffix=".lp", delete=False) as tmp:
            path = Path(tmp.name)

        try:
            # Translate Luna model to LP format
            LpTranslator.from_aq(
                model,
                filepath=path,
            )
            # Load LP file into SCIP
            scip_model.readProblem(path)  # type: ignore[no-untyped-call]
        finally:
            # Clean up temporary file
            if path.exists():
                path.unlink()

        # Run optimization
        scip_model.optimize()  # type: ignore[no-untyped-call]

        timing = timer.stop()

        # Check if model is infeasible
        if scip_model.getStatus() == "infeasible":  # type: ignore[no-untyped-call]
            raise InfeasibleModelError

        self._logger.info(f"Completed SCIP optimization for model {model.name} in {timing.total_seconds():.2f}s")

        # Translate SCIP solution back to Luna format
        return ZibTranslator.to_aq(
            scip_model,
            timing=timing,
            env=model.environment,
        )
