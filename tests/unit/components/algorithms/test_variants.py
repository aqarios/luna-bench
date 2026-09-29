"""Tests for the variant generators that expand one algorithm into many."""

import pytest
from pydantic import BaseModel, ValidationError

from luna_bench.algorithms.variants import ParameterGrid, ParameterList, apply_parameters
from luna_bench.errors.components.algorithms.unknown_parameter_path_error import UnknownParameterPathError


class TestParameterGrid:
    """A grid crosses every axis with every other, as sklearn's ParameterGrid does."""

    def test_single_axis_yields_one_combination_per_value(self) -> None:
        grid = ParameterGrid({"reps": [2, 4, 6]})

        assert list(grid) == [{"reps": 2}, {"reps": 4}, {"reps": 6}]

    def test_two_axes_yield_the_cartesian_product(self) -> None:
        grid = ParameterGrid({"reps": [2, 4], "shots": [8, 16]})

        assert list(grid) == [
            {"reps": 2, "shots": 8},
            {"reps": 2, "shots": 16},
            {"reps": 4, "shots": 8},
            {"reps": 4, "shots": 16},
        ]

    def test_len_matches_the_number_of_combinations_yielded(self) -> None:
        grid = ParameterGrid({"reps": [2, 4, 6], "shots": [8, 16]})

        assert len(grid) == len(list(grid)) == 6

    def test_iterating_twice_yields_the_same_combinations_in_the_same_order(self) -> None:
        grid = ParameterGrid({"reps": [2, 4], "shots": [8, 16]})

        assert list(grid) == list(grid)

    def test_a_list_of_grids_is_their_union(self) -> None:
        grid = ParameterGrid([{"reps": [2, 4]}, {"reps": [6], "shots": [8]}])

        assert list(grid) == [{"reps": 2}, {"reps": 4}, {"reps": 6, "shots": 8}]

    def test_a_range_is_accepted_as_an_axis(self) -> None:
        grid = ParameterGrid({"reps": range(1, 4)})

        assert list(grid) == [{"reps": 1}, {"reps": 2}, {"reps": 3}]

    def test_dotted_paths_are_kept_verbatim_as_axis_names(self) -> None:
        grid = ParameterGrid({"pipeline.xy_mixer.enable": [False, True]})

        assert list(grid) == [
            {"pipeline.xy_mixer.enable": False},
            {"pipeline.xy_mixer.enable": True},
        ]

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("basic", id="str"),
            pytest.param(b"basic", id="bytes"),
            pytest.param({"enable": True}, id="mapping"),
            pytest.param(4, id="scalar"),
        ],
    )
    def test_an_axis_value_that_is_not_a_sequence_is_rejected(self, value: object) -> None:
        with pytest.raises(TypeError, match="sequence"):
            ParameterGrid({"param_conversion": value})

    def test_an_empty_axis_is_rejected_rather_than_yielding_nothing(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            ParameterGrid({"reps": []})


class TestParameterList:
    """A list states complete configurations outright, with no product taken."""

    def test_each_dict_is_one_configuration(self) -> None:
        variants = ParameterList([{"reps": 2, "shots": 8}, {"reps": 6, "shots": 16}])

        assert list(variants) == [{"reps": 2, "shots": 8}, {"reps": 6, "shots": 16}]

    def test_len_matches_the_number_of_configurations(self) -> None:
        assert len(ParameterList([{"reps": 2}, {"reps": 6}])) == 2

    def test_a_sequence_value_is_applied_verbatim_rather_than_crossed(self) -> None:
        """The direct form is for values meant as-is, including genuinely list-valued fields."""
        variants = ParameterList([{"optimizer.bounds": [0.0, 1.0]}])

        assert list(variants) == [{"optimizer.bounds": [0.0, 1.0]}]

    def test_an_empty_list_of_configurations_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            ParameterList([])


class Inner(BaseModel):
    """Nested configuration, standing in for FlexQAOA's pipeline blocks."""

    enable: bool = True
    method: str = "ring"


class Outer(BaseModel):
    """Nested configuration one level further out."""

    inner: Inner = Inner()
    scaling: float = 2.0


class Algo(BaseModel):
    """Algorithm-shaped model, so the applier is tested without a backend."""

    reps: int = 1
    label: str = "base"
    outer: Outer = Outer()


class TestApplyParameters:
    """Applying one variant's parameters to the base algorithm."""

    def test_sets_a_top_level_field(self) -> None:
        applied = apply_parameters(Algo(), {"reps": 4})

        assert applied.reps == 4

    def test_sets_a_nested_field_through_a_dotted_path(self) -> None:
        applied = apply_parameters(Algo(), {"outer.inner.enable": False})

        assert applied.outer.inner.enable is False

    def test_leaves_the_fields_the_variant_does_not_name(self) -> None:
        applied = apply_parameters(Algo(), {"outer.inner.enable": False})

        assert applied.reps == 1
        assert applied.outer.inner.method == "ring"
        assert applied.outer.scaling == 2.0

    def test_applies_several_parameters_at_once(self) -> None:
        applied = apply_parameters(Algo(), {"reps": 6, "outer.scaling": 1.5})

        assert (applied.reps, applied.outer.scaling) == (6, 1.5)

    def test_does_not_mutate_the_base_algorithm(self) -> None:
        base = Algo()

        apply_parameters(base, {"reps": 8, "outer.inner.enable": False})

        assert base.reps == 1
        assert base.outer.inner.enable is True

    def test_validators_run_on_the_rebuilt_model(self) -> None:
        """A sequence where the field is an int is the direct form's own guard."""
        with pytest.raises(ValidationError):
            apply_parameters(Algo(), {"reps": [2, 4]})

    def test_an_unknown_top_level_path_is_rejected(self) -> None:
        with pytest.raises(UnknownParameterPathError, match="repetitions"):
            apply_parameters(Algo(), {"repetitions": 4})

    def test_an_unknown_nested_path_is_rejected(self) -> None:
        with pytest.raises(UnknownParameterPathError, match=r"outer\.inner\.enabled"):
            apply_parameters(Algo(), {"outer.inner.enabled": False})

    def test_a_path_through_a_field_that_is_not_a_model_is_rejected(self) -> None:
        with pytest.raises(UnknownParameterPathError, match=r"reps\.value"):
            apply_parameters(Algo(), {"reps.value": 4})


class TestApplyParametersKeepsWhatADumpWouldLose:
    """A dump does not round-trip a backend, so the applier must not rebuild from one."""

    def test_the_backend_survives_applying_a_variant(self) -> None:
        flexqaoa = pytest.importorskip("luna_quantum.algorithms").FlexQAOA
        aqarios_gpu = pytest.importorskip("luna_quantum.backends").AqariosGpu

        applied = apply_parameters(flexqaoa(backend=aqarios_gpu(), reps=1), {"reps": 6})

        assert applied.reps == 6
        assert isinstance(applied.backend, aqarios_gpu)

    def test_a_nested_pipeline_toggle_leaves_the_other_blocks_alone(self) -> None:
        flexqaoa = pytest.importorskip("luna_quantum.algorithms").FlexQAOA

        applied = apply_parameters(flexqaoa(), {"pipeline.xy_mixer.enable": False})

        assert applied.pipeline.xy_mixer.enable is False
        assert applied.pipeline.indicator_function.enable is True


class TestApplyParametersRejectsAMisspelledPathSegment:
    """A typo in the middle of a path is the realistic one: 'pipeline.xy_mixr.enable'."""

    def test_an_unknown_intermediate_segment_is_rejected(self) -> None:
        with pytest.raises(UnknownParameterPathError, match=r"outer\.middle\.enable"):
            apply_parameters(Algo(), {"outer.middle.enable": False})

    def test_the_error_names_the_fields_available_at_that_level(self) -> None:
        with pytest.raises(UnknownParameterPathError, match="inner"):
            apply_parameters(Algo(), {"outer.middle.enable": False})

    def test_a_path_reaching_through_a_field_that_is_not_a_model_is_rejected(self) -> None:
        with pytest.raises(UnknownParameterPathError, match=r"reps\.value\.deep"):
            apply_parameters(Algo(), {"reps.value.deep": 4})
