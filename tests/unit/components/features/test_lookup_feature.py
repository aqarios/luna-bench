from __future__ import annotations

from enum import StrEnum

import pytest
from luna_model import Model
from pydantic import ValidationError

from luna_bench.custom import (
    BaseModelLookupFeature,
    BaseValueLookupFeature,
    FeatureResult,
    LookupFeatureResult,
    feature,
)
from luna_bench.errors.model_lookup_miss_error import ModelLookupMissError
from tests.utils.luna_model import simple_model


class ProblemCategory(StrEnum):
    """Coarse problem family a model belongs to."""

    GRAPH = "graph"
    COMBINATORIAL = "combinatorial"
    SCHEDULING = "scheduling"
    ROUTING = "routing"


@feature
class CategoryFeature(BaseValueLookupFeature[ProblemCategory]):
    """Maps each model to a hand-assigned problem category."""


@feature
class DifficultyFeature(BaseValueLookupFeature[int]):
    """Hand-assigned difficulty rating per model."""


class FallbackResult(FeatureResult):
    """Custom result type carrying more than a bare value."""

    objective: float
    derived: bool


@feature
class FallbackFeature(BaseModelLookupFeature[float, FallbackResult]):
    """Lookup feature with a custom result type that computes a value on a miss."""

    def to_result(self, value: float, model: Model) -> FallbackResult:  # noqa: ARG002
        return FallbackResult(objective=value, derived=False)

    def on_miss(self, model: Model) -> FallbackResult:  # noqa: ARG002
        return FallbackResult(objective=-1.0, derived=True)


@pytest.fixture()
def model_a() -> Model:
    return simple_model("model_a")


@pytest.fixture()
def model_b() -> Model:
    return simple_model("model_b")


class TestPopulatingTheMapping:
    """The mapping is built from models, never from hashes typed by hand."""

    def test_add_model_registers_the_value(self, model_a: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)

        assert f.mapping == {hash(model_a): ProblemCategory.GRAPH}

    def test_add_model_accumulates_entries(self, model_a: Model, model_b: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)
        f.add_model(model_b, ProblemCategory.ROUTING)

        assert f.run(model_a).value == ProblemCategory.GRAPH
        assert f.run(model_b).value == ProblemCategory.ROUTING

    def test_add_model_replaces_an_existing_entry(self, model_a: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)
        f.add_model(model_a, ProblemCategory.SCHEDULING)

        assert f.run(model_a).value == ProblemCategory.SCHEDULING

    def test_add_models_accepts_a_mapping(self, model_a: Model, model_b: Model) -> None:
        f = CategoryFeature()
        f.add_models({model_a: ProblemCategory.GRAPH, model_b: ProblemCategory.COMBINATORIAL})

        assert f.run(model_a).value == ProblemCategory.GRAPH
        assert f.run(model_b).value == ProblemCategory.COMBINATORIAL

    def test_add_models_accepts_an_iterable_of_tuples(self, model_a: Model, model_b: Model) -> None:
        f = CategoryFeature()
        f.add_models([(model_a, ProblemCategory.GRAPH), (model_b, ProblemCategory.COMBINATORIAL)])

        assert f.run(model_a).value == ProblemCategory.GRAPH
        assert f.run(model_b).value == ProblemCategory.COMBINATORIAL


class TestRunningTheFeature:
    """A registered model yields its value; an unregistered one is loud about it."""

    def test_returns_the_registered_value(self, model_a: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.ROUTING)

        result = f.run(model_a)

        assert isinstance(result, LookupFeatureResult)
        assert result.value == ProblemCategory.ROUTING

    def test_covers_reports_membership(self, model_a: Model, model_b: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)

        assert f.covers(model_a) is True
        assert f.covers(model_b) is False

    def test_a_miss_raises_with_diagnostic_attributes(self, model_a: Model) -> None:
        f = CategoryFeature()

        with pytest.raises(ModelLookupMissError) as exc_info:
            f.run(model_a)

        error = exc_info.value
        assert error.model_name == "model_a"
        assert error.model_key == hash(model_a)
        assert error.feature_name == "CategoryFeature"
        assert "add_model" in str(error)

    def test_a_model_survives_the_encode_decode_round_trip(self, model_a: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)
        decoded = Model.decode(model_a.encode())

        assert f.covers(decoded) is True
        assert f.run(decoded).value == ProblemCategory.GRAPH

    def test_models_differing_only_in_name_get_distinct_entries(self, model_a: Model, model_b: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)

        assert f.covers(model_b) is False


class TestSerialization:
    """The feature is reconstructed from the database before a run, so it must round-trip."""

    def test_json_round_trip_restores_int_keys(self, model_a: Model) -> None:
        f = CategoryFeature()
        f.add_model(model_a, ProblemCategory.GRAPH)

        restored = CategoryFeature.model_validate_json(f.model_dump_json())

        assert restored.mapping == f.mapping
        assert all(isinstance(key, int) for key in restored.mapping)
        assert restored.run(model_a).value == ProblemCategory.GRAPH

    def test_an_invalid_value_is_rejected(self, model_a: Model) -> None:
        with pytest.raises(ValidationError):
            CategoryFeature.model_validate({"mapping": {hash(model_a): "not_a_category"}})

    def test_the_result_validates_the_value_type(self) -> None:
        with pytest.raises(ValidationError):
            CategoryFeature.result_cls(value="not_a_category")


class TestResultTypeBinding:
    """Each concrete subclass gets its own parametrized result type."""

    def test_subclasses_do_not_share_a_result_type(self) -> None:
        assert CategoryFeature.result_cls is not DifficultyFeature.result_cls
        assert CategoryFeature.result_cls is LookupFeatureResult[ProblemCategory]
        assert DifficultyFeature.result_cls is LookupFeatureResult[int]

    def test_the_bound_result_type_is_used_at_runtime(self, model_a: Model) -> None:
        f = DifficultyFeature()
        f.add_model(model_a, 3)

        result = f.run(model_a)

        assert type(result) is LookupFeatureResult[int]
        assert result.value == 3


class TestCustomResultAndMissHandling:
    """The two type parameters allow a custom result type and a computed fallback."""

    def test_a_hit_uses_the_custom_result_type(self, model_a: Model) -> None:
        f = FallbackFeature()
        f.add_model(model_a, 42.0)

        result = f.run(model_a)

        assert isinstance(result, FallbackResult)
        assert result.objective == 42.0
        assert result.derived is False

    def test_an_overridden_on_miss_returns_instead_of_raising(self, model_a: Model) -> None:
        result = FallbackFeature().run(model_a)

        assert result.objective == -1.0
        assert result.derived is True


class TestAbstractness:
    """The base classes are machinery, not usable features."""

    def test_the_model_lookup_base_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            BaseModelLookupFeature()  # type: ignore[abstract]

    def test_the_value_lookup_base_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            BaseValueLookupFeature()  # type: ignore[abstract]


class TestRegistration:
    """A concrete lookup feature registers like any other feature."""

    def test_the_feature_decorator_assigns_a_registered_id(self) -> None:
        assert CategoryFeature.registered_id.endswith("CategoryFeature")
