"""Tests for BarPlot generic class."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import numpy as np
from matplotlib import pyplot as plt

from luna_bench.custom import BaseFeature, FeatureResult
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.bar_plot import UNGROUPED_LABEL, BarPlot
from luna_bench.plots.utils.aggregation_enum import Aggregation
from luna_bench.plots.utils.style import REFERENCE_LINE_COLOUR, LunaColours

if TYPE_CHECKING:
    from matplotlib.text import Annotation

    from luna_bench.custom.types import FeatureClass


class FakeUseCaseResult(FeatureResult):
    """Feature result carrying an assigned value, like the lookup features do."""

    value: str


class FakeUseCaseFeature(BaseFeature[FakeUseCaseResult]):
    """Feature standing in for a per-model category assigned by the user."""

    def run(self, model: object) -> FakeUseCaseResult:
        """Unused; the results are provided directly in the tests."""
        raise NotImplementedError


class ConcreteBarPlot(BarPlot):
    """Concrete implementation of BarPlot for testing."""

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Test implementation for BarPlot."""


class TestBarPlot:
    """Test BarPlot functionality."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_minimal_data(self, mock_check_dep: MagicMock) -> None:
        """Test create with minimal required data."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show") as mock_show:
            plot = ConcreteBarPlot()
            rows = [
                {"algorithm": "Algo1", "value": 10},
                {"algorithm": "Algo2", "value": 20},
            ]

            plot.create(
                rows=rows,
                xlabel="Algorithm",
                ylabel="Value",
                title="Test",
            )

            mock_barplot.assert_called_once()
            mock_show.assert_called_once()

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_empty_rows_logs_warning(self, mock_check_dep: MagicMock) -> None:
        """Test create logs warning when rows is empty."""
        _ = mock_check_dep
        plot = ConcreteBarPlot()

        with patch.object(plot.logger, "warning") as mock_logger:
            plot.create(
                rows=[],
                xlabel="X",
                ylabel="Y",
                title="Test",
            )

            mock_logger.assert_called_once()

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_hue_grouping(self, mock_check_dep: MagicMock) -> None:
        """Test create with hue parameter for grouped bars."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [
                {"algorithm": "Algo1", "model": "ModelA", "value": 10},
                {"algorithm": "Algo1", "model": "ModelB", "value": 15},
                {"algorithm": "Algo2", "model": "ModelA", "value": 20},
            ]

            plot.create(
                rows=rows,
                xlabel="Algorithm",
                ylabel="Value",
                title="Test",
                hue="model",
                x="algorithm",
                y="value",
            )

            mock_barplot.assert_called_once()
            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["hue"] == "model"

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_hline(self, mock_check_dep: MagicMock) -> None:
        """Test create adds horizontal reference line."""
        _ = mock_check_dep
        with (
            patch("seaborn.barplot"),
            patch("matplotlib.pyplot.show"),
            patch("matplotlib.pyplot.axhline") as mock_axhline,
        ):
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hline=5.0,
                hline_label="Reference",
            )

            mock_axhline.assert_called_once()
            call_kwargs = mock_axhline.call_args[1]
            assert call_kwargs["y"] == 5.0
            assert call_kwargs["label"] == "Reference"

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_different_aggregations(self, mock_check_dep: MagicMock) -> None:
        """Test create with different aggregation strategies."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [
                {"algorithm": "Algo1", "value": 10},
                {"algorithm": "Algo1", "value": 20},
            ]

            for aggregation in [Aggregation.MEAN, Aggregation.MAX, Aggregation.MIN, Aggregation.MEAN_SD]:
                plt.close("all")
                plot.create(
                    rows=rows,
                    xlabel="X",
                    ylabel="Y",
                    title="Test",
                    aggregation=aggregation,
                )

                call_kwargs = mock_barplot.call_args[1]
                assert call_kwargs["estimator"] == aggregation.estimator
                assert call_kwargs["errorbar"] == aggregation.errorbar

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_ylim(self, mock_check_dep: MagicMock) -> None:
        """Test create with y-axis limits."""
        _ = mock_check_dep
        with patch("seaborn.barplot"), patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.ylim") as mock_ylim:
            plot = ConcreteBarPlot()
            plot.annotate = False
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                ylim=(0, 100),
            )

            mock_ylim.assert_called_once_with(0, 100)

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_adds_headroom_for_annotations(self, mock_check_dep: MagicMock) -> None:
        """Test annotated bars get extra room above the requested y limits."""
        _ = mock_check_dep
        with patch("seaborn.barplot"), patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.ylim") as mock_ylim:
            plot = ConcreteBarPlot()
            plot.annotate = True
            plot.annotate_headroom = 0.5
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", ylim=(0, 100))

            mock_ylim.assert_called_once_with(0, 150)

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_annotates_every_bar_with_the_formatted_value(self, mock_check_dep: MagicMock) -> None:
        """Test each bar carries its aggregated value, formatted as configured."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            plot.annotate_format = "{:.1f}%"
            rows = [
                {"algorithm": "Algo1", "value": 10.0},
                {"algorithm": "Algo2", "value": 20.0},
            ]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value")

            texts = [text.get_text() for text in plt.gca().texts]
            assert texts == ["10.0%", "20.0%"]

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_draws_an_unlabelled_baseline(self, mock_check_dep: MagicMock) -> None:
        """Test the baseline is a solid black line that stays out of the legend."""
        _ = mock_check_dep
        with (
            patch("seaborn.barplot"),
            patch("matplotlib.pyplot.show"),
            patch("matplotlib.pyplot.axhline") as mock_axhline,
            patch("matplotlib.pyplot.legend") as mock_legend,
        ):
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", baseline=0.0, errorbar=None)

            mock_axhline.assert_called_once_with(y=0.0, color=REFERENCE_LINE_COLOUR, linewidth=1.0)
            mock_legend.assert_not_called()

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_caps_the_error_bars(self, mock_check_dep: MagicMock) -> None:
        """Test the error bars are drawn with caps so they read as a T."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            plot.errorbar_capsize = 0.3
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test")

            assert mock_barplot.call_args[1]["capsize"] == 0.3

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_places_annotations_above_the_error_bars(self, mock_check_dep: MagicMock) -> None:
        """Test an annotation clears the error bar of its own bar instead of overlapping it."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [
                {"algorithm": "Algo1", "value": 5.0},
                {"algorithm": "Algo1", "value": 15.0},
            ]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value")

            ax = plt.gca()
            errorbar_top = max(max(np.asarray(line.get_ydata(), dtype=float).tolist()) for line in ax.lines)
            annotation_y = cast("Annotation", ax.texts[0]).xy[1]
            assert annotation_y == errorbar_top
            assert annotation_y > 10.0  # above the mean, i.e. above the bar itself

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_skips_annotations_when_disabled(self, mock_check_dep: MagicMock) -> None:
        """Test annotations can be turned off."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            plot.annotate = False
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value")

            assert list(plt.gca().texts) == []

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_without_legend(self, mock_check_dep: MagicMock) -> None:
        """Test create doesn't include legend by default."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                legend=False,
            )

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["legend"] is False

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_colours_ungrouped_bars_uniformly(self, mock_check_dep: MagicMock) -> None:
        """Test bars without a hue all share the default Aqarios blue."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [
                {"algorithm": "Algo1", "value": 10},
                {"algorithm": "Algo2", "value": 20},
                {"algorithm": "Algo3", "value": 30},
            ]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value")

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["color"] == LunaColours.LUNA_SOLVE
            assert "palette" not in call_kwargs

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_spreads_gradient_over_groups(self, mock_check_dep: MagicMock) -> None:
        """Test grouped bars are coloured by the Luna gradient across the groups."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [
                {"algorithm": "Algo1", "value": 10, "Use case": "knapsack"},
                {"algorithm": "Algo2", "value": 20, "Use case": "maxcut"},
                {"algorithm": "Algo3", "value": 30, "Use case": "tsp"},
            ]

            plot.create(
                rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value", hue="Use case", legend=True
            )

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["hue"] == "Use case"
            assert call_kwargs["palette"] == LunaColours.palette(3)

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_fixed_color_skips_palette(self, mock_check_dep: MagicMock) -> None:
        """Test an explicit color keeps all bars in a single colour."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            plot.color = LunaColours.LUNA_SOLVE
            rows = [{"algorithm": "Algo1", "value": 10}, {"algorithm": "Algo2", "value": 20}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value")

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["color"] == LunaColours.LUNA_SOLVE
            assert "palette" not in call_kwargs

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_forwards_seaborn_kwargs(self, mock_check_dep: MagicMock) -> None:
        """Test extra keyword arguments reach seaborn and override the defaults."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                capsize=0.2,
                palette=["#000000"],
            )

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["capsize"] == 0.2
            assert call_kwargs["palette"] == ["#000000"]

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_explicit_errorbar(self, mock_check_dep: MagicMock) -> None:
        """Test an explicit errorbar overrides the one derived from the aggregation."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", errorbar=("ci", 95))

            assert mock_barplot.call_args[1]["errorbar"] == ("ci", 95)

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_adds_errorbar_to_legend_only_when_shown(self, mock_check_dep: MagicMock) -> None:
        """Test the error bar legend entry is absent when no error bars are drawn."""
        _ = mock_check_dep
        with patch("seaborn.barplot"), patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.legend") as mock_leg:
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", errorbar="sd")
            assert mock_leg.call_args[1]["labels"] == ["± 1 SD"]

            mock_leg.reset_mock()
            plt.close("all")
            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", errorbar=None)
            mock_leg.assert_not_called()

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_with_legend(self, mock_check_dep: MagicMock) -> None:
        """Test create with legend enabled."""
        _ = mock_check_dep
        with patch("seaborn.barplot") as mock_barplot, patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                legend=True,
            )

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["legend"] is True


class TestBarPlotGrouping:
    """Test splitting bars along a per-model feature."""

    def _benchmark_results(self, values: dict[str, object]) -> MagicMock:
        """Build benchmark results whose feature container serves *values* per model."""
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

    def test_apply_grouping_without_group_by_is_a_no_op(self) -> None:
        """Test rows are untouched when no grouping feature is configured."""
        plot = ConcreteBarPlot()
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        assert plot.apply_grouping(self._benchmark_results({"m1": "Maxcut"}), rows) == {}
        assert rows == [{"algorithm": "Algo1", "model": "m1", "value": 10}]

    def test_apply_grouping_adds_column_and_hue(self) -> None:
        """Test each row is tagged with its model's feature value."""
        plot = ConcreteBarPlot()
        plot.group_by = cast("FeatureClass", FakeUseCaseFeature)
        plot.group_label = "Use case"
        rows = [
            {"algorithm": "Algo1", "model": "m1", "value": 10},
            {"algorithm": "Algo1", "model": "m2", "value": 20},
        ]

        kwargs = plot.apply_grouping(self._benchmark_results({"m1": "Maxcut", "m2": "Mis"}), rows)

        assert kwargs == {"hue": "Use case", "legend": True}
        assert [row["Use case"] for row in rows] == ["Maxcut", "Mis"]

    def test_apply_grouping_labels_models_without_a_value(self) -> None:
        """Test models the feature has no result for stay visible as 'unknown'."""
        plot = ConcreteBarPlot()
        plot.group_by = cast("FeatureClass", FakeUseCaseFeature)
        rows = [
            {"algorithm": "Algo1", "model": "m1", "value": 10},
            {"algorithm": "Algo1", "model": "m2", "value": 20},
        ]

        plot.apply_grouping(self._benchmark_results({"m1": "Maxcut", "m2": None}), rows)

        assert [row["FakeUseCase"] for row in rows] == ["Maxcut", UNGROUPED_LABEL]

    def test_apply_grouping_falls_back_when_feature_is_missing(self) -> None:
        """Test a feature that produced no results leaves the plot ungrouped."""
        plot = ConcreteBarPlot()
        plot.group_by = cast("FeatureClass", FakeUseCaseFeature)
        rows = [{"algorithm": "Algo1", "model": "m1", "value": 10}]

        with patch.object(plot.logger, "warning") as mock_warning:
            kwargs = plot.apply_grouping(self._benchmark_results({"m1": None}), rows)

        assert kwargs == {}
        assert rows == [{"algorithm": "Algo1", "model": "m1", "value": 10}]
        mock_warning.assert_called_once()
