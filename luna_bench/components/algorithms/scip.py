import tempfile
from logging import Logger
from pathlib import Path
from typing import ClassVar

from luna_quantum import Logging, Model, Solution, Timer
from luna_quantum.translator import LpTranslator
from pyscipopt import Model as PyScipModel

from luna_bench.base_components import BaseAlgorithmSync
from luna_bench.helpers import algorithm


class InfeasibleModelError(Exception):
    """
    Exception raised when a model solved by SCIP is identified as infeasible.

    This indicates that no feasible solution exists for the given constraints.
    """

    def __init__(self) -> None:
        msg = "Model is infeasible. No solution possible."
        super().__init__(msg)


@algorithm()
class ScipAlgorithm(BaseAlgorithmSync):
    """
    Classical exact optimization algorithm using SCIP (Solving Constraint Integer Programs).

    This algorithm wraps the SCIP solver to provide exact solutions for optimization
    problems using classical branch-and-bound methods. It translates Luna quantum models
    to LP format, solves them with SCIP, and translates the results back.

    Parameters
    ----------
    max_runtime: int | None
        Defines the maximum runtime for the SCIP solver in seconds.
    quiet_output: bool
        Defines the verbosity of the SCIP solver output.
    _logger: Logger
        Class-level logger for tracking algorithm execution.

    Raises
    ------
    InfeasibleModelError: If the model has no feasible solution.
    """

    max_runtime: int | None = None
    quiet_output: bool = True

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    def run(self, model: Model) -> Solution:
        """
        Solve an optimization model using the SCIP classical solver.

        Parameters
        ----------
        model : Model
            The Luna optimization model to solve.

        Returns
        -------
        Solution
            Solution object containing the optimal variable assignments,
            objective value, and timing information.

        Raises
        ------
        InfeasibleModelError
            If SCIP determines the model is infeasible.

        Examples
        --------
        >>> scip_algo = ScipAlgorithm()
        >>> solution = scip_algo.run(my_model)
        """
        scip_model = PyScipModel()
        scip_model.hideOutput(quiet=self.quiet_output)

        if self.max_runtime is not None:
            scip_model.setParam("limits/time", self.max_runtime)  # type: ignore[no-untyped-call]

        timer = Timer.start()

        self._logger.info(f"Running SCIP for model {model.name}")

        # Create temporary LP file for SCIP
        with tempfile.NamedTemporaryFile(suffix=".lp", delete=False) as tmp:
            path = Path(tmp.name)

        try:
            LpTranslator.from_aq(
                model,
                filepath=path,
            )
            scip_model.readProblem(path)  # type: ignore[no-untyped-call]
        finally:
            if path.exists():
                path.unlink()

        scip_model.optimize()  # type: ignore[no-untyped-call]

        timing = timer.stop()

        if scip_model.getStatus() == "infeasible":  # type: ignore[no-untyped-call]
            raise InfeasibleModelError

        self._logger.info(f"Completed SCIP optimization for model {model.name} in {timing.total_seconds:.2f}s")

        # Extract solution values from SCIP model
        solution_dict = {}
        for var in scip_model.getVars():  # type: ignore[no-untyped-call]
            solution_dict[var.name] = scip_model.getVal(var)  # type: ignore[no-untyped-call]

        objective_value = scip_model.getObjVal()  # type: ignore[no-untyped-call]

        return Solution.from_dict(
            data=solution_dict,
            model=model,
            timing=timing,
            energy=objective_value,
        )
