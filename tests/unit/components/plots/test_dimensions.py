"""Tests for the groupings a bar plot can be split along."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from luna_bench.custom import BaseFeature, FeatureResult, feature
from luna_bench.custom.result_containers.algorithm_result_container import AlgorithmResultContainer
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.dimensions import (
    UNGROUPED_LABEL,
    AlgorithmDimension,
    FeatureDimension,
    ModelDimension,
    ParameterDimension,
)


class UseCaseResult(FeatureResult):
    """Feature result carrying an assigned value, like the lookup features do."""

    value: str


@feature
class UseCaseFeature(BaseFeature[UseCaseResult]):
    """Feature standing in for a per-model category assigned by the user."""

    def run(self, model: object) -> UseCaseResult:
        """Unused; the results are provided directly in the tests."""
        raise NotImplementedError


def _with_features(values: dict[str, str | None]) -> MagicMock:
    """Return results whose models have the given feature values."""
    benchmark_results = MagicMock(spec=BenchmarkResultContainer)
    benchmark_results.features = {}
    for model_name, value in values.items():
        container = MagicMock()
        if value is None:
            container.first.side_effect = KeyError(model_name)
        else:
            container.first.return_value = SimpleNamespace(value=value)
        benchmark_results.features[model_name] = container
    return benchmark_results


def _with_algorithms(configurations: dict[str, object]) -> MagicMock:
    """Return results whose algorithms carry the given configurations."""
    benchmark_results = MagicMock(spec=BenchmarkResultContainer)
    benchmark_results.algorithms = {
        "m1": {
            name: MagicMock(spec=AlgorithmResultContainer, algorithm=configuration)
            for name, configuration in configurations.items()
        }
    }
    return benchmark_results


class TestColumnDimensions:
    """Test grouping along a column the rows already carry."""

    def test_the_column_becomes_the_hue(self) -> None:
        """Test a column needs no benchmark data at all."""
        rows = [
            {"algorithm": "Algo1", "model": "m1", "value": 10},
            {"algorithm": "Algo1", "model": "m2", "value": 20},
        ]

        assert ModelDimension().resolve(MagicMock(spec=BenchmarkResultContainer), rows) == "model"
        assert rows == [
            {"algorithm": "Algo1", "model": "m1", "value": 10},
            {"algorithm": "Algo1", "model": "m2", "value": 20},
        ]

    def test_the_algorithm_column_groups_the_other_way_round(self) -> None:
        """Test a plot whose bars are the models is split per algorithm."""
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        assert AlgorithmDimension().resolve(MagicMock(spec=BenchmarkResultContainer), rows) == "algorithm"

    def test_a_label_renames_the_column(self) -> None:
        """Test the legend title becomes a column of its own, so seaborn can show it."""
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        column = ModelDimension(label="Instance").resolve(MagicMock(spec=BenchmarkResultContainer), rows)

        assert column == "Instance"
        assert rows[0]["Instance"] == "m1"

    def test_a_missing_column_returns_no_column(self) -> None:
        """Test a plot whose rows carry no model is drawn rather than refused."""
        rows = [{"algorithm": "Algo1", "value": 10}]

        with patch("luna_bench.plots.dimensions.logger.warning") as mock_warning:
            assert ModelDimension().resolve(MagicMock(spec=BenchmarkResultContainer), rows) is None

        mock_warning.assert_called_once()


class TestFeatureDimension:
    """Test grouping along a value looked up per model."""

    def test_every_row_is_tagged_with_its_models_value(self) -> None:
        """Test the group comes from the feature, not from anything in the rows."""
        rows = [
            {"algorithm": "Algo1", "model": "m1", "value": 10},
            {"algorithm": "Algo1", "model": "m2", "value": 20},
        ]

        column = FeatureDimension(feature=UseCaseFeature, label="Use case").resolve(
            _with_features({"m1": "Maxcut", "m2": "Mis"}), rows
        )

        assert column == "Use case"
        assert [row["Use case"] for row in rows] == ["Maxcut", "Mis"]

    def test_the_label_defaults_to_the_feature_name(self) -> None:
        """Test a legend title is not needed for the plot to say what it grouped by."""
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        column = FeatureDimension(feature=UseCaseFeature).resolve(_with_features({"m1": "Maxcut"}), rows)

        assert column == "UseCase"

    def test_models_without_a_value_stay_visible(self) -> None:
        """Test a model the feature has no result for is grouped rather than dropped."""
        rows = [
            {"algorithm": "Algo1", "model": "m1", "value": 10},
            {"algorithm": "Algo1", "model": "m2", "value": 20},
        ]

        FeatureDimension(feature=UseCaseFeature).resolve(_with_features({"m1": "Maxcut", "m2": None}), rows)

        assert [row["UseCase"] for row in rows] == ["Maxcut", UNGROUPED_LABEL]

    def test_a_feature_without_results_returns_no_column(self) -> None:
        """Test a feature that produced nothing leaves the plot drawable."""
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        with patch("luna_bench.plots.dimensions.logger.warning") as mock_warning:
            assert FeatureDimension(feature=UseCaseFeature).resolve(_with_features({"m1": None}), rows) is None

        assert rows == [{"algorithm": "Algo1", "model": "m1", "value": 10}]
        mock_warning.assert_called_once()

    def test_another_attribute_can_be_read(self) -> None:
        """Test a feature result that is not a lookup value can still group."""
        benchmark_results = MagicMock(spec=BenchmarkResultContainer)
        benchmark_results.features = {"m1": MagicMock(first=lambda _: SimpleNamespace(var_number=12))}
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        FeatureDimension(feature=UseCaseFeature, attribute="var_number").resolve(benchmark_results, rows)

        assert rows[0]["UseCase"] == "12"

    def test_the_feature_is_stored_by_its_id(self) -> None:
        """Test a class is not JSON, so it is stored as the id it is registered under."""
        grouper = FeatureDimension(feature=UseCaseFeature)

        assert grouper.model_dump()["feature"] == UseCaseFeature.registered_id
        assert FeatureDimension.model_validate(grouper.model_dump()).feature is UseCaseFeature


class TestParameterDimension:
    """Test grouping along a setting the algorithms were configured with."""

    def test_the_groups_are_named_after_the_setting(self) -> None:
        """Test the legend says which value of the parameter a bar belongs to."""
        rows = [
            {"algorithm": "qaoa_p1", "model": "m1", "value": 1},
            {"algorithm": "qaoa_p3", "model": "m1", "value": 3},
        ]

        column = ParameterDimension(parameter="reps").resolve(
            _with_algorithms({"qaoa_p1": SimpleNamespace(reps=1), "qaoa_p3": SimpleNamespace(reps=3)}), rows
        )

        assert column == "reps"
        assert [row["reps"] for row in rows] == ["reps=1", "reps=3"]

    def test_only_the_algorithms_with_the_setting_are_plotted(self) -> None:
        """Test a classical baseline is dropped rather than drawn without a group."""
        rows = [
            {"algorithm": "scip", "model": "m1", "value": 0},
            {"algorithm": "qaoa_p2", "model": "m1", "value": 2},
        ]

        ParameterDimension(parameter="reps").resolve(
            _with_algorithms({"scip": SimpleNamespace(), "qaoa_p2": SimpleNamespace(reps=2)}), rows
        )

        assert [row["algorithm"] for row in rows] == ["qaoa_p2"]

    def test_the_groups_are_ordered_by_the_setting(self) -> None:
        """Test the groups read low to high, whatever order the rows arrived in."""
        rows = [
            {"algorithm": "qaoa_p10", "model": "m1", "value": 10},
            {"algorithm": "qaoa_p2", "model": "m1", "value": 2},
        ]

        ParameterDimension(parameter="reps").resolve(
            _with_algorithms({"qaoa_p10": SimpleNamespace(reps=10), "qaoa_p2": SimpleNamespace(reps=2)}), rows
        )

        assert [row["reps"] for row in rows] == ["reps=2", "reps=10"]

    def test_a_label_titles_the_legend(self) -> None:
        """Test the legend can be titled in the terms of the algorithm."""
        rows = [{"algorithm": "qaoa_p1", "model": "m1", "value": 1}]

        column = ParameterDimension(parameter="reps", label="QAOA layers").resolve(
            _with_algorithms({"qaoa_p1": SimpleNamespace(reps=1)}), rows
        )

        assert column == "QAOA layers"
        assert rows[0]["QAOA layers"] == "reps=1"

    @pytest.mark.parametrize(
        "configuration", [SimpleNamespace(), SimpleNamespace(reps=True), SimpleNamespace(reps="3")]
    )
    def test_a_setting_that_is_not_a_number_is_no_setting(self, configuration: Any) -> None:  # noqa: ANN401
        """Test a flag is not mistaken for a swept number just because bool is an int."""
        rows = [{"algorithm": "qaoa_p1", "model": "m1", "value": 1}]

        with patch("luna_bench.plots.dimensions.logger.warning") as mock_warning:
            assert (
                ParameterDimension(parameter="reps").resolve(_with_algorithms({"qaoa_p1": configuration}), rows) is None
            )

        assert rows == [{"algorithm": "qaoa_p1", "model": "m1", "value": 1}]
        mock_warning.assert_called_once()


class TestDimensionEdges:
    """Test what the groupers do with data they cannot group."""

    def test_a_container_that_holds_no_bars_is_skipped(self) -> None:
        """Test the annotation walk ignores whatever else is on the axes."""
        from luna_bench.plots.generics.bar_plot import BarPlot

        class _Plot(BarPlot):
            def run(self, benchmark_results: object, save_dir: str | None = None) -> None:
                """Unused."""

        axes = MagicMock(containers=[MagicMock()], lines=[])

        _Plot()._annotate_bars(axes)

        axes.annotate.assert_not_called()

    def test_a_line_whose_coordinates_do_not_pair_up_is_no_error_bar(self) -> None:
        """Test a stray artist on the axes cannot be read as an error bar."""
        from luna_bench.plots.generics.bar_plot import BarPlot

        line = SimpleNamespace(get_xdata=lambda: [0.0, 1.0], get_ydata=lambda: [0.0])

        assert BarPlot._errorbar_tops(MagicMock(lines=[line])) == []
