from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from luna_quantum.translator import LpTranslator
from pyscipopt import Model as ScipModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature

if TYPE_CHECKING:
    from luna_quantum import Model


class InfeasibleModelError(Exception):
    """Infeasible exception is raised inside the model solved by SCIP is identified to be infeasible."""

    def __init__(self) -> None:
        msg = "Model is infeasible. No solution possible. Cannot be used to calculate metrics in subsequent calls."
        super().__init__(msg)


class OptSolFeatureResult(ArbitraryDataDomain):
    """
    Result container for optimal solution feature calculations.

    Attributes
    ----------
    best_sol : float
        The best objective value found by the SCIP solver. This is either the
        optimal solution or the best feasible solution found within the time limit.
    pre_terminated : bool
        Indicates whether the solver terminated early due to reaching the time limit.
        If True, best_sol represents an upper bound rather than the proven optimum.
    """

    best_sol: float
    pre_terminated: bool
    runtime: float


@feature
class OptSolFeature(IFeature):
    """
    Feature that computes the optimal (or best feasible) solution for optimization models.

    This feature translates a Luna-Model to LP format and solves it using the
    SCIP mixed-integer programming solver. It can be configured with a maximum runtime
    to obtain upper bounds for computationally expensive problems.

    Attributes
    ----------
    max_runtime : int | None, optional
        Maximum solver runtime in seconds. If None (default), the solver runs until
        optimality is proven or infeasibility is detected. If set, the solver may
        return a suboptimal solution marked with pre_terminated=True.

    Raises
    ------
    InfeasibleModelError
        If the model has no feasible solution.

    Examples
    --------
    >>> # Solve to optimality (no time limit)
    >>> feature = OptSolFeature()
    >>> result = feature.run(model)
    >>> print(f"Optimal value: {result.best_sol}")

    >>> # Get best solution within 60 seconds
    >>> feature = OptSolFeature(max_runtime=60)
    >>> result = feature.run(model)
    >>> if result.pre_terminated:
    ...     print(f"Upper bound: {result.best_sol}")
    ... else:
    ...     print(f"Optimal value: {result.best_sol}")
    """

    max_runtime: float | None = None  # define max runtime in seconds

    def run(self, model: Model) -> OptSolFeatureResult:
        """
        Calculate the optimal solution for the given model, or at least get an upper bound.

        This method performs the following steps:
        1. Translates the Luna Quantum model to LP format via a temporary file
        2. Reads the LP file into a SCIP solver instance
        3. Configures the time limit (if specified)
        4. Solves the optimization problem
        5. Returns the best objective value and termination status

        Parameters
        ----------
        model: Model
            The model for which the feature should be calculated

        Returns
        -------
        OptSolFeatureResult
            Contains the best objective value found and whether the solver
            terminated early due to time limit.

        Notes
        -----
        - For large or difficult problems, consider setting max_runtime to avoid
          excessive computation time
        - When pre_terminated is True, the returned best_sol is an upper bound
          (for minimization) or lower bound (for maximization) on the optimal value
        """
        scip_model = ScipModel()
        if self.max_runtime is not None:
            scip_model.setParam("limits/time", self.max_runtime)  # type: ignore[no-untyped-call]

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
        if scip_model.getStatus() == "infeasible":  # type: ignore[no-untyped-call]
            raise InfeasibleModelError

        # translate model to
        pre_terminated = False
        if scip_model.getStatus() == "timelimit":  # type: ignore[no-untyped-call]
            pre_terminated = True

        return OptSolFeatureResult(
            best_sol=scip_model.getObjVal(),  # type: ignore[no-untyped-call]
            pre_terminated=pre_terminated,
            runtime=scip_model.getSolvingTime(),  # type: ignore[no-untyped-call]
        )
