import pytest
from _pytest.fixtures import FixtureRequest
from luna_quantum import Model, Variable


def _dummy_model(name: str) -> Model:
    model = Model(name)
    with model.environment:
        x = Variable("x")
        y = Variable("y")
    model.objective = x * y + x
    model.constraints += x >= 0
    model.constraints += y <= 5

    return model


@pytest.fixture()
def model(request: FixtureRequest) -> Model:
    name: str = getattr(request, "param", "default_model")

    return _dummy_model(name)
