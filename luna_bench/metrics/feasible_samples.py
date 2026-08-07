"""Feasible Samples metric counting the feasible and the total samples of a solution."""

from luna_model import Solution
from pydantic import Field

from luna_bench.custom import BaseMetric, FeatureResultContainer, MetricResult, metric


class FeasibleSamplesResult(MetricResult):
    """Result container for the Feasible Samples metric.

    Attributes
    ----------
    num_feasible_samples : int
        Number of samples that satisfy every constraint of the model.
    num_samples : int
        Total number of samples the algorithm returned.
    """

    num_feasible_samples: int = Field(ge=0, description="Number of samples satisfying all constraints.")
    num_samples: int = Field(ge=0, description="Total number of samples returned by the algorithm.")


@metric
class FeasibleSamples(BaseMetric[FeasibleSamplesResult]):
    """Metric that counts the feasible samples and the total samples of a solution.

    Unlike ``FeasibilityRatio``, which reduces a run to a single fraction, this metric
    keeps both counts. That preserves how much sampling went into a result, so several
    runs can be pooled afterwards - summing the counts weights every sample equally,
    whereas averaging per-model ratios weights a ten-sample model like a thousand-sample
    one.

    Examples
    --------
    >>> from luna_bench.metrics import FeasibleSamples
    >>> metric = FeasibleSamples()
    >>> result = metric.run(solution, feature_results)
    >>> print(f"{result.num_feasible_samples} of {result.num_samples} samples feasible")

    Notes
    -----
    Feasibility is taken from the ``Solution`` object, which is typically computed by the
    solver or by model evaluation.

    See Also
    --------
    FeasibilityRatio : The same information as a single ratio per run.
    """

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> FeasibleSamplesResult:  # noqa: ARG002
        """Count the feasible and the total samples of the given solution.

        Parameters
        ----------
        solution : Solution
            The solution object containing samples from an algorithm run.
        feature_results : FeatureResultContainer
            Container with pre-computed feature results (not used by this metric).

        Returns
        -------
        FeasibleSamplesResult
            Contains the number of feasible samples and the total number of samples.
        """
        num_samples = len(solution.samples)
        if num_samples == 0:
            return FeasibleSamplesResult(num_feasible_samples=0, num_samples=0)
        return FeasibleSamplesResult(
            num_feasible_samples=len(solution.filter_feasible().samples),
            num_samples=num_samples,
        )
