"""Best Solution Found metric for extracting the best feasible objective value."""

from luna_model import Solution
from luna_model.solution import ValueSource
from pydantic import Field

from luna_bench.custom import BaseMetric, FeatureResultContainer, MetricResult, metric


class BestSolutionFoundResult(MetricResult):
    """Result container for the Best Solution Found metric.

    Attributes
    ----------
    best_solution_found : float
        The best feasible objective value found in the solution set.
        Returns inf if no feasible solution is found.
    """

    best_solution_found: float = Field(description="The best feasible objective value found.")


@metric()
class BestSolutionFound(BaseMetric[BestSolutionFoundResult]):
    r"""Metric that extracts the Best Solution Found (BSF).

    The Best Solution Found metric extracts the best feasible objective value from
    the solution set. The best value is the lowest objective value for minimization
    problems and the highest for maximization problems, considering only feasible
    samples.

    Unlike :class:`BestSolutionFoundRatio`, this metric reports the raw best feasible
    value and does not require an optimal solution for comparison.

    Attributes
    ----------
    value_source : ValueSource
        Defines whether the objective values or the raw energy values from the
        algorithm should be used to determine the best solution. Default is
        ValueSource.OBJ.

    Examples
    --------
    >>> from luna_bench.metrics import BestSolutionFound
    >>> metric = BestSolutionFound()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"Best Solution Found: {result.best_solution_found}")
    """

    value_source: ValueSource = ValueSource.OBJ

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> BestSolutionFoundResult:  # noqa: ARG002
        """Extract the best feasible objective value for the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
        feature_results : FeatureResultContainer
            Container with pre-computed feature results. Unused by this metric.

        Returns
        -------
        BestSolutionFoundResult
            Contains the best feasible objective value. Returns inf if no feasible
            solution is available.

        Raises
        ------
        ValueError
            If the solution is None.
        """
        if solution is None:
            msg = "Solution must not be None."
            raise ValueError(msg)

        # best() already returns the best *feasible* result for the given sense.
        best = solution.best()
        if best is None:
            return BestSolutionFoundResult(best_solution_found=float("inf"))

        best_view = best[0]
        value = best_view.obj_value if self.value_source == ValueSource.OBJ else best_view.raw_energy
        if value is None:
            return BestSolutionFoundResult(best_solution_found=float("inf"))

        return BestSolutionFoundResult(best_solution_found=float(value))
