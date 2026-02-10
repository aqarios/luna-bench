from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from luna_quantum import Sense

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature, OptSolFeatureResult

from luna_quantum import Bounds, Model, Solution, Timer, Variable, Vtype, Unbounded
import time


def create_solution(
    obj_values: list[float],
    sense: Sense = Sense.Min,
    runtime_seconds: float = 0.1,
    feasible: list[bool] | None = None,
) -> Solution:
    """Create a mock Solution with specific objective values."""
    assert len(obj_values) == len(feasible) if feasible is not None else True
    timer = Timer.start()
    time.sleep(runtime_seconds)
    timing = timer.stop()

    m = Model('MockModel')
    m.set_sense(sense)
    with m.environment:
        x = Variable('x', vtype=Vtype.Real, bounds=Bounds(lower=Unbounded, upper=Unbounded))
        y = Variable('y', vtype = Vtype.Integer)
    m.objective += x
    m.add_constraint(y == 0)
    x_data = [{'x': x_val, 'y':0} for x_val in obj_values]
    m.add_constraint(y == 0)
    if feasible is not None:
        for i, feas in enumerate(feasible):
            x_data[i]['y'] = 0 if feas else 1
    return Solution.from_dicts(
        data = x_data,
        model = m,
        timing = timing,
    )




@pytest.fixture()
def mock_feature_results(request: FixtureRequest) -> MagicMock:
    """Create a mock FeatureResults object with a given optimal solution value.

    Use with ``@pytest.mark.parametrize("mock_feature_results", [10.0], indirect=True)``.
    """
    optimal_value: float = getattr(request, "param", 0.0)

    opt_sol_result = OptSolFeatureResult(best_sol=optimal_value, pre_terminated=False)
    opt_sol_feature = OptSolFeature()

    feature_results = MagicMock(spec=FeatureResults)
    feature_results.first.return_value = (opt_sol_result, opt_sol_feature)

    return feature_results


@pytest.fixture()
def mock_metric_solution(request: FixtureRequest) -> MagicMock:
    """Create a mock Solution object with configurable sense and expectation value.

    Use with ``@pytest.mark.parametrize("mock_metric_solution", [(Sense.Min, 5.0)], indirect=True)``.
    The param should be a tuple of ``(sense, expectation_value)``.
    ``expectation_value=None`` creates an empty solution.
    """
    sense: Sense
    expectation_value: float | None
    sense, expectation_value = getattr(request, "param", (Sense.Min, None))

    solution = MagicMock(spec=["best", "sense", "expectation_value", "samples"])
    solution.sense = sense

    if expectation_value is None:
        solution.best.return_value = None
        solution.expectation_value.return_value = None
        solution.samples = []
    else:
        best_sample = MagicMock()
        solution.best.return_value = best_sample
        solution.expectation_value.return_value = expectation_value
        solution.samples = [best_sample]

    return solution
