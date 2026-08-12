from enum import StrEnum


class MetricDirection(StrEnum):
    """Which end of a metric's scale is the better one.

    Declared per metric class so consumers that rank, sort or plot metric results know
    whether a larger value means a better run.

    - HIGHER_IS_BETTER: A larger value is the better result, e.g. a ratio against a
      known optimum.
    - LOWER_IS_BETTER: A smaller value is the better result, e.g. a runtime.
    - DEPENDS_ON_SENSE: The metric has a better end, but which one it is depends on the
      sense of the model - typically because the metric reports a raw objective value, so
      the lower value is better when minimizing and the higher when maximizing. Such a
      metric cannot be ranked across models of different senses, and a consumer that
      ranks or plots it has to read the sense and settle the direction itself. Prefer a
      metric that normalizes the model away, such as `ApproximationRatio`, when results
      have to be compared across models.
    - INDIFFERENT: The metric has no better or worse end at all, e.g. a plain sample
      count. This is the default, so a metric that has not been classified is never
      mistaken for one with a genuine direction.

    Note the difference between the last two: `DEPENDS_ON_SENSE` says there is a better
    value but the metric alone cannot say which, while `INDIFFERENT` says the question
    does not apply.
    """

    HIGHER_IS_BETTER = "HigherIsBetter"
    LOWER_IS_BETTER = "LowerIsBetter"
    DEPENDS_ON_SENSE = "DependsOnSense"
    INDIFFERENT = "Indifferent"
