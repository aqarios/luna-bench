from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from luna_model.translator import LpTranslator

from luna_bench.custom import BaseModelLookupFeature, FeatureResult, feature
from luna_bench.errors.infeasible_model_error import InfeasibleModelError
from luna_bench.helpers.optional_dependencies import check_optional_dependency

if TYPE_CHECKING:
    from luna_model import Model, Solution


class OptSolFeatureResult(FeatureResult):
    """
    Result container for optimal solution feature calculations.

    This is also what a known optimum is registered as on `OptSolFeature`, since a
    precomputed value carries exactly what a solved one does. Storing only these
    scalars keeps the record trivially JSON-serializable - so a populated
    `OptSolFeature` persists inside a luna-bench benchmark database without any custom
    encoding - and sidesteps reconstructing a full :class:`~luna_model.Solution`
    (which would be formulation-specific). Equivalent formulations of one instance
    share the same optimum, so the same value applies to each of their models,
    registered individually via
    :meth:`~luna_bench.custom.BaseModelLookupFeature.add_model`.

    Attributes
    ----------
    global_best_sol : float
        The best objective value found by the SCIP solver, or the best-known value
        registered for the model. This is either the optimal solution or the best
        feasible solution found within the time limit.
    pre_terminated : bool
        Indicates whether the solver terminated early due to reaching the time limit.
        If True, best_sol represents an upper bound rather than the proven optimum.
        Registering a value, set it True for a best-known but unproven value (e.g. a
        QOBLIB ``.bst`` file) and leave it False for a proven optimum, so a consumer
        can tell the two apart.
    runtime : float
        Seconds the solver spent. Defaults to zero, which is what a registered value
        keeps: it was looked up rather than solved for.
    """

    global_best_sol: float
    pre_terminated: bool = False
    runtime: float = 0.0

    @classmethod
    def from_solution(cls, solution: Solution, *, pre_terminated: bool) -> OptSolFeatureResult:
        """Create a result from a luna solution, taking the objective of its best sample.

        Intended for registering a known optimum that is held as a solution rather than
        as a bare number, so ``runtime`` stays zero.

        Parameters
        ----------
        solution : Solution
            The solution to read the best objective value from.
        pre_terminated : bool
            Whether the value is a best-known bound rather than a proven optimum.

        Returns
        -------
        OptSolFeatureResult
            The result carrying that objective value.

        Raises
        ------
        ValueError
            If the solution has no feasible sample, or its best sample has no
            objective value.
        """
        best = solution.best()
        if not best:
            msg = "The solution object contains no feasible sample."
            raise ValueError(msg)
        objective = best[0].obj_value
        if objective is None:
            msg = "The best sample has no objective value."
            raise ValueError(msg)
        return cls(global_best_sol=objective, pre_terminated=pre_terminated)


@feature
class OptSolFeature(BaseModelLookupFeature[OptSolFeatureResult, OptSolFeatureResult]):
    """
    Feature that computes the optimal (or best feasible) solution for optimization models.

    This feature translates a Luna-Model to LP format and solves it using the
    SCIP mixed-integer programming solver. It can be configured with a maximum runtime
    to obtain upper bounds for computationally expensive problems.

    Solving is expensive, and for many benchmark instances the optimal solution is
    already known (e.g. shipped alongside the model), so re-solving is wasteful.
    Register those known values as `OptSolFeatureResult` records with
    :meth:`~luna_bench.custom.BaseModelLookupFeature.add_model` /
    :meth:`~luna_bench.custom.BaseModelLookupFeature.add_models`, and the feature serves
    them directly instead of solving. A model with no registered value is solved as
    usual, so an unpopulated feature behaves exactly as it always has.

    The mapping is keyed by ``hash(model)``, which covers the model's name as well as
    its contents and survives the ``encode()``/``decode()`` round-trip a benchmark
    performs before running features. Populate it *before* handing the feature to
    ``Benchmark.add_feature()``: the benchmark serializes the feature's configuration at
    that point, so entries added afterwards never reach the run. Use
    :meth:`~luna_bench.custom.BaseModelLookupFeature.covers` to check a modelset up front
    rather than discovering gaps as unexpected solves mid-run.

    Attributes
    ----------
    max_runtime : float | None, optional
        Maximum solver runtime in seconds. If None (default), the solver runs until
        optimality is proven or infeasibility is detected. If set, the solver may
        return a suboptimal solution marked with pre_terminated=True. Ignored for a
        model whose value is precomputed.
    quiet_output: bool
        Defines the verbosity of the SCIP solver output. Ignored for a model whose
        value is precomputed.
    mapping : dict[int, OptSolFeatureResult]
        Inherited. ``hash(model)`` to precomputed result; populate it with
        ``add_model``/``add_models`` rather than by hand.

    Raises
    ------
    InfeasibleModelError
        If the model has no precomputed value and the solver proves it infeasible.

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``
    (only needed for models that have to be solved).

    Examples
    --------
    >>> # Solve to optimality (no time limit)
    >>> feature = OptSolFeature()
    >>> result = feature.run(model)
    >>> print(f"Optimal value: {result.global_best_sol}")

    >>> # Get best solution within 60 seconds
    >>> feature = OptSolFeature(max_runtime=60)
    >>> result = feature.run(model)
    >>> if result.pre_terminated:
    ...     print(f"Upper bound: {result.global_best_sol}")
    ... else:
    ...     print(f"Optimal value: {result.global_best_sol}")

    >>> # Reuse a known optimum, skipping the solver
    >>> feature = OptSolFeature()
    >>> feature.add_model(model, OptSolFeatureResult(global_best_sol=42.0))
    >>> feature.run(model).global_best_sol
    42.0

    >>> # A known solution rather than a bare number
    >>> feature.add_model(other, OptSolFeatureResult.from_solution(solution, pre_terminated=False))

    >>> # Register a whole collection at once, then check for gaps up front
    >>> feature = OptSolFeature()
    >>> feature.add_models(collection.get_precomp_solutions())
    >>> unsolved = [m for m in modelset.models if not feature.covers(m)]
    """

    max_runtime: float | None = None  # define max runtime in seconds
    quiet_output: bool = True

    if TYPE_CHECKING:
        # --- generated by scripts/type_hints.py, do not edit by hand ---
        # Mirrors the pydantic fields so IDEs show every option on the constructor.
        # Never executed: pydantic builds the real ``__init__``.
        def __init__(
            self,
            *,
            mapping: dict[int, OptSolFeatureResult] = {},  # noqa: B006
            max_runtime: float | None = None,
            quiet_output: bool = True,
        ) -> None: ...

    def to_result(self, value: OptSolFeatureResult, model: Model) -> OptSolFeatureResult:  # noqa: ARG002
        """
        Report a registered value as this run's feature result.

        A registered value is already an `OptSolFeatureResult`, so it only has to be
        handed back. It is copied rather than returned as-is, so that a consumer holding
        the result cannot reach back into the mapping and change what later runs see.

        Parameters
        ----------
        value : OptSolFeatureResult
            The result registered for ``model``.
        model : Model
            The model the value was looked up for. Unused - the value carries
            everything the result needs.

        Returns
        -------
        OptSolFeatureResult
            A copy of the registered value.
        """
        return value.model_copy()

    def on_miss(self, model: Model) -> OptSolFeatureResult:
        """
        Calculate the optimal solution for the given model, or at least get an upper bound.

        Called for any model without a precomputed value, which is every model unless
        the mapping has been populated. Overrides the base's raising behaviour: a missing
        entry is not an error here, just the expensive path.

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
        check_optional_dependency("pyscipopt")
        from pyscipopt import Model as ScipModel  # noqa: PLC0415

        scip_model = ScipModel()
        scip_model.hideOutput(quiet=self.quiet_output)
        if self.max_runtime is not None:
            scip_model.setParam("limits/time", self.max_runtime)

        with tempfile.NamedTemporaryFile(suffix=".lp", delete=False) as tmp:
            path = Path(tmp.name)

        try:
            LpTranslator.from_lm(
                model,
                filepath=path,
            )
            scip_model.readProblem(path)
        finally:
            if path.exists():
                path.unlink()

        scip_model.optimize()
        if scip_model.getStatus() == "infeasible":
            raise InfeasibleModelError

        # translate model to
        pre_terminated = False
        if scip_model.getStatus() == "timelimit":
            pre_terminated = True

        return OptSolFeatureResult(
            global_best_sol=scip_model.getObjVal(),
            pre_terminated=pre_terminated,
            runtime=scip_model.getSolvingTime(),
        )
