"""Best Solution Found metric for evaluating solution quality against optimal solutions.

Metric implemented from https://arxiv.org/pdf/2405.07624
"""

from luna_model import Sense, Solution
from pydantic import Field

from luna_bench.custom import BaseMetric, FeatureResultContainer, MetricResult, metric
from luna_bench.features import OptSolFeature
from luna_bench.helpers import get_ratio


class BestSolutionFoundRatioResult(MetricResult):
    """Result container for the Best Solution Found metric.

    Attributes
    ----------
    best_solution_found : float
        The calculated best solution found ratio. A value of 1.0 indicates the
        optimal solution was found. For both minimization and maximization problems,
        values > 1.0 indicate worse solution quality.
        Returns inf if no solution was found.
    """

    best_solution_found: float = Field(ge=1.0, description="The calculated best solution found ratio.")


@metric(OptSolFeature)
class BestSolutionFoundRatio(BaseMetric[BestSolutionFoundRatioResult]):
    r"""Metric that calculates the Best Solution Found (BSF) ratio against the optimal.

    The Best Solution Found metric measures how close the best sample in a solution
    is to the optimal solution. Unlike the Approximation Ratio which uses the
    expectation value (average energy), this metric uses only the best sample found.

    The relative cost :math:`c(X)` of the BSF in comparison to the optimal solution is:

    .. math::

        c(X) = \frac{\min_{x \in X} C(x)}{C(x^*)}

    Where:
    - :math:`C(x)` is the objective value of solution :math:`x`,
    - :math:`C(x^*)` is the objective value of the optimal solution :math:`x^*`,
    - :math:`\min_{x \in X} C(x)` represents the best solution found in sample set :math:`X`.

    For minimization problems:
        BSF = best_found_value / optimal_value

    For maximization problems:
        BSF = optimal_value / best_found_value

    Interpretation:
        - BSF = 1.0 means the best sample equals optimal
        - BSF > 1.0 means the best sample is worse than optimal

    Attributes
    ----------
    abs_tol : float
        Absolute tolerance for considering a value as zero. Used to prevent
        division by zero errors. Default is 1e-3.

    Examples
    --------
    >>> from luna_bench.metrics import BestSolutionFoundRatio
    >>> metric = BestSolutionFoundRatio()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Best Solution Found ratio: {result.best_solution_found}")

    Notes
    -----
    This metric requires the OptSolFeature to be computed first, which provides
    the optimal solution value for comparison.

    **Source**: https://arxiv.org/pdf/2405.07624
    """

    abs_tol: float = 1e-3

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> BestSolutionFoundRatioResult:
        """Calculate the Best Solution Found ratio for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
        feature_results : FeatureResultContainer
            Container with pre-computed feature results. Must include results
            from OptSolFeature which provides the optimal solution value.

        Returns
        -------
        BestSolutionFoundRatioResult
            Contains the calculated BSF ratio. Returns inf value if no
            solution samples are available.

        Raises
        ------
        NotImplementedError
            If the denominator (optimal value for Min, best found value for Max)
            is close to zero (within abs_tol tolerance).
        """
        # Get the optimal solution from features
        opt_sol = feature_results.first(feature_cls=OptSolFeature)
        if solution is None:
            msg = "Solution must not be None."
            raise ValueError(msg)

        # best() already returns the best *feasible* result for the given sense.
        best = solution.best()
        if best is None:
            return BestSolutionFoundRatioResult(best_solution_found=float("inf"))

        best_view = best[0]
        if best_view.obj_value is None:
            return BestSolutionFoundRatioResult(best_solution_found=float("inf"))

        best_value = float(best_view.obj_value)
        if solution.sense == Sense.MIN:
            bsf = get_ratio(nominator=best_value, denominator=opt_sol.global_best_sol, abt_diff=self.abs_tol)
        else:
            bsf = get_ratio(nominator=opt_sol.global_best_sol, denominator=best_value, abt_diff=self.abs_tol)

        return BestSolutionFoundRatioResult(best_solution_found=bsf)
