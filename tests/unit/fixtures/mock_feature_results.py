import time
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from luna_model import Bounds, Model, Sense, Solution, Timer, Unbounded, Variable, Vtype

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeatureResult

SolutionFactory = Callable[..., Solution]


@pytest.fixture()
def create_solution() -> SolutionFactory:
    """Fixture factory for creating Solution objects with specific objective values.

    Use as a callable in tests::

        def test_example(create_solution):
            solution = create_solution(obj_values=[1.0, 2.0], sense=Sense.Min)
    """

    def _build_solution(
        obj_values: list[float],
        sense: Sense = Sense.MIN,
        runtime_seconds: float = 0.1,
        feasible: list[bool] | None = None,
        *,
        set_runtime: bool = True,
    ) -> Solution:
        assert len(obj_values) == len(feasible) if feasible is not None else True
        if set_runtime:
            timer = Timer.start()
            time.sleep(runtime_seconds)
            timing = timer.stop()
        else:
            timing = None

        m = Model("MockModel")
        m.sense = sense
        with m.environment:
            x = Variable("x", vtype=Vtype.REAL, bounds=Bounds(lower=Unbounded, upper=Unbounded))
            y = Variable("y", vtype=Vtype.INTEGER)
        m.objective += x
        m.add_constraint(y == 0)
        x_data = [{x: x_val, y: 0} for x_val in obj_values]
        m.add_constraint(y == 0)
        if feasible is not None:
            for i, feas in enumerate(feasible):
                x_data[i][y] = 0 if feas else 1
        return Solution.from_dicts(data=x_data, model=m, timing=timing)

    return _build_solution


@pytest.fixture()
def mock_feature_results(request: FixtureRequest) -> MagicMock:
    """Create a mock FeatureResults object with a given optimal solution value.

    Use with ``@pytest.mark.parametrize("mock_feature_results", [10.0], indirect=True)``.
    """
    optimal_value: float = getattr(request, "param", 0.0)

    opt_sol_result = OptSolFeatureResult(best_sol=optimal_value, pre_terminated=False, runtime=0.01)

    feature_results = MagicMock(spec=FeatureResults)
    feature_results.first.return_value = opt_sol_result

    return feature_results


@pytest.fixture()
def mock_solution_config(request: FixtureRequest) -> MagicMock:
    """Create a mock Solution object with configurable sense and expectation value.

    Use with ``@pytest.mark.parametrize("mock_solution_config", [(Sense.Min, 5.0)], indirect=True)``.
    The param should be a tuple of ``(sense, expectation_value)``.
    ``expectation_value=None`` creates an empty solution.
    """
    sense: Sense
    expectation_value: float | None
    sense, expectation_value = getattr(request, "param", (Sense.MIN, None))

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
