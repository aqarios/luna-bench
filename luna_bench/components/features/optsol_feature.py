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
    """Fake feature result class."""

    best_sol: float
    pre_terminated: bool


@feature
class OptSolFeature(IFeature):
    """Optimum feature class."""

    max_runtime: int | None = None  # define max runtime in seconds

    def run(self, model: Model) -> OptSolFeatureResult:
        """
        Calculate the optimal solution for the given model, or at least get an upper bound.

        Parameters
        ----------
        model: Model
            The model for which the feature should be calculated

        """
        scip_model = ScipModel()
        _, path = tempfile.mkstemp(suffix=".lp")
        LpTranslator.from_aq(
            model,
            filepath=Path(path),
        )
        if self.max_runtime is not None:
            scip_model.setParam("limits/time", self.max_runtime)

        scip_model.readProblem(path)
        scip_model.optimize()

        if scip_model.getStatus() == "infeasible":
            raise InfeasibleModelError

        # translate model to
        pre_terminated = False
        if scip_model.getStatus() == "timelimit":
            pre_terminated = True

        return OptSolFeatureResult(best_sol=scip_model.getObjVal(), pre_terminated=pre_terminated)
