"""Tests for BarPlot generic class."""

import logging
from typing import TYPE_CHECKING, Any, ClassVar, cast
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_hex
from matplotlib.patches import Rectangle

from luna_bench.custom import BaseFeature, FeatureResult, feature
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.errors.components.plots import PlotMissingValuesError
from luna_bench.plots.dimensions import MetricDimension, ModelDimension
from luna_bench.plots.generics.bar_plot import BarPlot
from luna_bench.plots.plot_style import Annotation, ErrorBars, Figure, Missing
from luna_bench.plots.utils.aggregation_enum import Aggregation
from luna_bench.plots.utils.errorbar import AUTO_ERRORBAR
from luna_bench.plots.utils.style import REFERENCE_LINE_COLOUR, LunaColours

if TYPE_CHECKING:
    from matplotlib.text import Annotation as MatplotlibAnnotation


class FakeUseCaseResult(FeatureResult):
    """Feature result carrying an assigned value, like the lookup features do."""

    value: str


class FakeUseCaseFeature(BaseFeature[FakeUseCaseResult]):
    """Feature standing in for a per-model category assigned by the user."""

    def run(self, model: object) -> FakeUseCaseResult:
        """Unused; the results are provided directly in the tests."""
        raise NotImplementedError


@feature
class RegisteredUseCaseFeature(BaseFeature[FakeUseCaseResult]):
    """A registered stand-in, so a stored id can be resolved back into the class."""

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

            for aggregation in [Aggregation.MEAN, Aggregation.MAX, Aggregation.MIN]:
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
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                ylim=(0, 100),
            )

            mock_ylim.assert_called_once_with(0, 100)

    def test_requested_limits_stay_the_scale_the_axis_is_read_in(self) -> None:
        """Test the room for the labels is added past the last tick, not to the scale.

        A ratio is bounded at 100%, so the axis is not given ticks past it - but the
        labels still belong inside the frame.
        """
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=Annotation(headroom=0.5))

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 100.0}],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
            ylim=(0, 100),
        )

        axes = plt.gca()
        assert max(axes.get_yticks()) == 100
        # Room above the last tick, so the annotation of a full bar is not outside.
        assert axes.get_ylim()[1] > 100
        assert axes.get_ylim()[0] == 0

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_unannotated_limits_are_exactly_what_was_asked_for(self, mock_check_dep: MagicMock) -> None:
        """Test a plot whose bars stay under its limits is given exactly those limits.

        The room above is for what stands there - the labels, a cap, a reference line -
        and a plot with none of them past the limit is not given any.
        """
        _ = mock_check_dep
        with patch("seaborn.barplot"), patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.ylim") as mock_ylim:
            plot = ConcreteBarPlot(annotation=None)

            plot.create(rows=[{"algorithm": "Algo1", "value": 10}], xlabel="X", ylabel="Y", title="T", ylim=(0, 100))

            mock_ylim.assert_called_once_with(0, 100)

    def test_limits_grow_to_cover_an_error_bar_that_passes_them(self) -> None:
        """Test a spread reaching past a bounded axis is shown rather than cut off.

        The cap of an error bar is a fact about the run: a share whose models scatter
        around 100% has one above it, and an axis that stopped at the limit would hide it.
        """
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=None)

        plot.create(
            rows=[{"algorithm": "Algo1", "value": value} for value in (100.0, 100.0, 85.0)],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
            errorbar="sd",
            ylim=(0, 100),
        )

        axes = plt.gca()
        cap = max(top for _, top in BarPlot._errorbar_tops(axes))
        assert cap > 100.0
        assert axes.get_ylim()[1] > cap
        # Still the scale it was asked for: the room above the limit stays unlabelled.
        assert max(axes.get_yticks()) == 100

    def test_limits_grow_so_a_reference_line_is_not_drawn_onto_the_frame(self) -> None:
        """Test the line an axis is bounded at stays readable as a line."""
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=None)

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 50.0}],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
            errorbar=None,
            hline=100.0,
            ylim=(0, 100),
        )

        assert plt.gca().get_ylim()[1] > 100.0

    def test_headroom_grows_an_axis_that_was_left_to_the_data(self) -> None:
        """Test a plot without limits of its own still makes room for its labels."""
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=Annotation(headroom=0.5))

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 10.0}],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
        )

        # Above the bar, and nowhere below it: an empty margin under the bars would say a
        # value could have been there.
        bottom, top = plt.gca().get_ylim()
        assert top > 10.0
        assert bottom == 0.0

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_annotates_every_bar_with_the_formatted_value(self, mock_check_dep: MagicMock) -> None:
        """Test each bar carries its aggregated value, formatted as configured."""
        _ = mock_check_dep
        # Neither written nor shown, so the figure stays open to be read back.
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=Annotation(format="{:.1f}%"))
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
            plot = ConcreteBarPlot(errorbars=ErrorBars(capsize=0.3))
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test")

            assert mock_barplot.call_args[1]["capsize"] == 0.3

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_places_annotations_above_the_error_bars(self, mock_check_dep: MagicMock) -> None:
        """Test an annotation clears the error bar of its own bar instead of overlapping it."""
        _ = mock_check_dep
        # Neither written nor shown, so the figure stays open to be read back.
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=Annotation())
        rows = [
            {"algorithm": "Algo1", "value": 5.0},
            {"algorithm": "Algo1", "value": 15.0},
        ]

        plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value")

        ax = plt.gca()
        errorbar_top = max(max(np.asarray(line.get_ydata(), dtype=float).tolist()) for line in ax.lines)
        annotation_y = cast("MatplotlibAnnotation", ax.texts[0]).xy[1]
        assert annotation_y == errorbar_top
        assert annotation_y > 10.0  # above the mean, i.e. above the bar itself

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_writes_no_annotations_by_default(self, mock_check_dep: MagicMock) -> None:
        """Test a bar chart is read off its axis unless the exact values are the point."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"):
            plot = ConcreteBarPlot()
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
            plot.figure.color = LunaColours.LUNA_SOLVE
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
        plot = ConcreteBarPlot(figure=Figure(show=False))
        rows = [{"algorithm": "Algo1", "value": 10.0}, {"algorithm": "Algo1", "value": 20.0}]

        plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value", errorbar="sd")
        legend = plt.gca().get_legend()
        assert legend is not None
        assert [text.get_text() for text in legend.get_texts()] == ["± 1 SD"]

        plt.close("all")
        plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", x="algorithm", y="value", errorbar=None)
        assert plt.gca().get_legend() is None

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


class TestBarPlotDraw:
    """Test that the declared display fields reach `create`."""

    def test_draw_forwards_the_declared_fields(self) -> None:
        """Test the fields of the plot are what create is called with."""
        plot = ConcreteBarPlot(
            x=ModelDimension(),
            y=MetricDimension(
                "runtime",
                "Runtime (s)",
                limits=(0, 2),
                reference=1.0,
                reference_label="Optimal",
                baseline=0.0,
            ),
            figure=Figure(title="Runtime"),
            aggregation=Aggregation.MAX,
        )
        rows = [{"model": "m1", "runtime": 1.5}]

        with patch.object(ConcreteBarPlot, "create") as mock_create:
            plot.draw(benchmark_results=MagicMock(spec=BenchmarkResultContainer), rows=rows, save_dir="out")

        mock_create.assert_called_once_with(
            save_dir="out",
            rows=rows,
            x="model",
            y="runtime",
            xlabel="Model",
            ylabel="Runtime (s)",
            title="Runtime",
            aggregation=Aggregation.MAX,
            errorbar=AUTO_ERRORBAR,
            hline=1.0,
            hline_label="Optimal",
            baseline=0.0,
            ylim=(0.0, 2.0),
        )

    def test_draw_overrides_win_over_the_fields(self) -> None:
        """Test a caller can still override a declared value per call."""
        plot = ConcreteBarPlot(figure=Figure(title="Declared"))

        with patch.object(ConcreteBarPlot, "create") as mock_create:
            plot.draw(
                benchmark_results=MagicMock(spec=BenchmarkResultContainer),
                rows=[{"algorithm": "Algo1", "value": 1}],
                title="Overridden",
            )

        assert mock_create.call_args.kwargs["title"] == "Overridden"

    def test_draw_applies_the_row_transformation(self) -> None:
        """Test a subclass can reduce its rows without reimplementing run."""

        class PoolingBarPlot(ConcreteBarPlot):
            def transform_rows(
                self, rows: list[dict[str, Any]], x: str | None, group: str | None
            ) -> list[dict[str, Any]]:
                _ = x, group
                return [{"algorithm": "pooled", "value": sum(row["value"] for row in rows)}]

        plot = PoolingBarPlot()

        with patch.object(PoolingBarPlot, "create") as mock_create:
            plot.draw(
                benchmark_results=MagicMock(spec=BenchmarkResultContainer),
                rows=[{"algorithm": "Algo1", "value": 1}, {"algorithm": "Algo2", "value": 2}],
            )

        assert mock_create.call_args.kwargs["rows"] == [{"algorithm": "pooled", "value": 3}]


class TestBarPlotAnnotationText:
    """Test how an annotated value is written."""

    def test_the_format_decides_by_default(self) -> None:
        """Test nothing changes for a plot that does not ask for plain decimals."""
        assert ConcreteBarPlot().annotation_text(0.0000567) == "5.67e-05"

    def test_decimals_replace_scientific_notation(self) -> None:
        """Test a small value can be written plainly, which is what makes bars comparable."""
        assert ConcreteBarPlot(annotation=Annotation(max_decimals=6)).annotation_text(0.0000567) == "0.000057"

    def test_trailing_zeros_are_dropped(self) -> None:
        """Test the setting is a limit, not a fixed width."""
        assert ConcreteBarPlot(annotation=Annotation(max_decimals=6)).annotation_text(0.25) == "0.25"
        assert ConcreteBarPlot(annotation=Annotation(max_decimals=6)).annotation_text(12.0) == "12"

    def test_a_value_too_small_to_show_keeps_its_format(self) -> None:
        """Test a value that would round to zero is written in scientific notation instead."""
        assert ConcreteBarPlot(annotation=Annotation(max_decimals=3)).annotation_text(0.0000567) == "5.67e-05"

    def test_zero_is_written_as_zero(self) -> None:
        """Test an exact zero is not mistaken for a value too small to show."""
        assert ConcreteBarPlot(annotation=Annotation(max_decimals=3)).annotation_text(0.0) == "0"

    def test_the_font_size_reaches_the_annotations(self) -> None:
        """Test the annotations can be made to fit a crowded axis."""
        plot = ConcreteBarPlot(figure=Figure(show=False), annotation=Annotation(fontsize=6, max_decimals=4))

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 0.25}], xlabel="X", ylabel="Y", title="T", x="algorithm", y="value"
        )

        annotation = plt.gca().texts[0]
        assert annotation.get_fontsize() == 6
        assert annotation.get_text() == "0.25"


class TestBarPlotColours:
    """Test that the bars are drawn in the colours the palette says."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_the_bar_colour_is_the_brand_colour_exactly(self) -> None:
        """Test seaborn does not dim the fill, which would miss the brand blue."""
        plot = ConcreteBarPlot(figure=Figure(show=False))

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 10}], xlabel="X", ylabel="Y", title="T", x="algorithm", y="value"
        )

        bars = [patch for patch in plt.gca().patches if isinstance(patch, Rectangle) and patch.get_height()]
        assert to_hex(bars[0].get_facecolor()).upper() == LunaColours.LUNA_SOLVE

    def test_the_saturation_can_still_be_tuned(self) -> None:
        """Test the passthrough reaches an argument the plot sets itself."""
        plot = ConcreteBarPlot(figure=Figure(show=False, seaborn_kwargs={"saturation": 0.5}))

        with patch("seaborn.barplot") as mock_barplot:
            plot.create(rows=[{"algorithm": "Algo1", "value": 10}], xlabel="X", ylabel="Y", title="T")

        assert mock_barplot.call_args.kwargs["saturation"] == 0.5


class TestMissingValues:
    """Test what a plot does with values it cannot draw."""

    ROWS: ClassVar[list[dict[str, Any]]] = [
        {"algorithm": "Algo1", "value": 1.0},
        {"algorithm": "Algo1", "value": 3.0},
        {"algorithm": "Algo2", "value": float("inf")},
        {"algorithm": "Algo2", "value": None},
    ]

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def _draw(self, plot: ConcreteBarPlot) -> None:
        plot.create(rows=list(self.ROWS), xlabel="X", ylabel="Y", title="T", x="algorithm", y="value")

    def test_a_missing_value_is_left_out_and_marked_by_default(self) -> None:
        """Test the figure is drawn, and says what it could not draw.

        The default carries on without changing what the bars mean - the values are as
        absent as under ``"drop"`` - and puts what happened to them on the figure rather
        than only in the log.
        """
        self._draw(ConcreteBarPlot(figure=Figure(show=False)))

        axes = plt.gca()
        assert [text.get_text() for text in axes.texts] == ["2"]
        assert [patch.get_hatch() for patch in axes.patches if patch.get_hatch()] == ["//"]

    def test_a_missing_value_is_refused_when_asked_for(self) -> None:
        """Test a benchmark can still say a missing value means no figure at all."""
        with pytest.raises(PlotMissingValuesError, match="Algo2: 2"):
            self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="raise")))

    def test_dropping_leaves_the_drawable_values(self) -> None:
        """Test the bar of the algorithm that kept its values is unaffected by the other one."""
        plot = ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="drop"))

        with patch("seaborn.barplot") as mock_barplot:
            self._draw(plot)

        drawn = mock_barplot.call_args.kwargs["data"]
        assert list(drawn["value"]) == [1.0, 3.0]
        # The category is named anyway, so its mark lands under a slot of its own.
        assert mock_barplot.call_args.kwargs["order"] == ["Algo1", "Algo2"]

    def test_filling_draws_them_past_the_largest_value(self) -> None:
        """Test a pandas aggregate of what could be drawn, scaled by the factor."""
        plot = ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="max", factor=1.1))

        with patch("seaborn.barplot") as mock_barplot:
            self._draw(plot)

        assert list(mock_barplot.call_args.kwargs["data"]["value"]) == pytest.approx([1.0, 3.0, 3.3, 3.3])

    def test_the_default_factor_puts_a_fill_past_the_bars_rather_than_on_them(self) -> None:
        """Test ``"max"`` lands above the tallest bar without being asked to.

        A fill exactly at the largest value is indistinguishable in height from a real
        maximum, which is the one thing the factor exists to prevent.
        """
        plot = ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="max"))

        with patch("seaborn.barplot") as mock_barplot:
            self._draw(plot)

        assert list(mock_barplot.call_args.kwargs["data"]["value"]) == pytest.approx([1.0, 3.0, 3.3, 3.3])

    def test_filling_takes_a_constant_as_well(self) -> None:
        """Test a plain number fills with itself, unscaled."""
        plot = ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy=0.0))

        with patch("seaborn.barplot") as mock_barplot:
            self._draw(plot)

        assert list(mock_barplot.call_args.kwargs["data"]["value"]) == [1.0, 3.0, 0.0, 0.0]

    def test_dropping_says_nothing_on_the_figure(self) -> None:
        """Test the empty slot is the whole statement, and the log carries the rest."""
        self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="drop")))

        axes = plt.gca()
        assert [text.get_text() for text in axes.texts] == []
        assert [patch for patch in axes.patches if patch.get_hatch()] == []

        legend = axes.get_legend()
        labels = [text.get_text() for text in legend.get_texts()] if legend else []
        assert not any("missing" in label for label in labels)

        # The category keeps its place, so the gap is where the algorithm was - and the
        # axis keeps showing it, which it would not if it scaled to the bars it drew.
        assert [label.get_text() for label in axes.get_xticklabels()] == ["Algo1", "Algo2"]
        assert axes.get_xlim()[1] >= 1.0

    def test_the_category_is_marked_with_how_many_it_lost(self) -> None:
        """Test the figure says the values were there, and how many."""
        self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="mark")))

        axes = plt.gca()
        assert [text.get_text() for text in axes.texts] == ["2"]
        legend = axes.get_legend()
        assert legend is not None
        assert "missing values (2)" in [text.get_text() for text in legend.get_texts()]

    def test_a_filled_bar_is_always_marked(self) -> None:
        """Test a bar drawn at the fill is not left looking like a measured one."""
        self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="max")))

        axes = plt.gca()
        assert [text.get_text() for text in axes.texts] == ["2"]
        # Marked, but not struck through: the bar is there, it is only not measured.
        assert [patch for patch in axes.patches if patch.get_hatch()] == []

    def test_the_mark_can_be_turned_off(self) -> None:
        """Test a figure that only wants the bars, with the warning left to the log."""
        self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="max", mark=False)))

        assert [text.get_text() for text in plt.gca().texts] == []

    def test_a_warning_names_the_categories(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the log says how many values were lost and which bars they belonged to."""
        with caplog.at_level(logging.WARNING):
            self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="drop")))

        assert "2 of 4 values of 'value'" in caplog.text
        assert "Algo2: 2" in caplog.text

    def test_marking_leaves_them_out_and_strikes_the_category_through(self) -> None:
        """Test a solver that reported nothing is not read as one with a short bar."""
        plot = ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="mark"))

        with patch("seaborn.barplot") as mock_barplot:
            self._draw(plot)

        # Left out, exactly as "drop" leaves them out.
        assert list(mock_barplot.call_args.kwargs["data"]["value"]) == [1.0, 3.0]

    def test_the_marked_category_is_struck_through(self) -> None:
        """Test the band over the category, on top of the cross and the count."""
        self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="mark")))

        axes = plt.gca()
        legend = axes.get_legend()
        assert legend is not None
        assert "missing values (2)" in [text.get_text() for text in legend.get_texts()]
        assert [patch.get_hatch() for patch in axes.patches if patch.get_hatch()] == ["//"]

    def test_no_mark_takes_the_strike_through_away_as_well(self) -> None:
        """Test turning the marks off leaves the figure with nothing but its bars."""
        self._draw(ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="mark", mark=False)))

        axes = plt.gca()
        assert [text.get_text() for text in axes.texts] == []
        assert [patch for patch in axes.patches if patch.get_hatch()] == []

    def test_only_the_group_that_lost_values_is_struck_through(self) -> None:
        """Test a use case that reported nothing does not take its neighbours with it."""
        rows = [
            {"algorithm": "Algo1", "use": "A", "value": 1.0},
            {"algorithm": "Algo1", "use": "B", "value": 2.0},
            {"algorithm": "Algo2", "use": "A", "value": float("inf")},
            {"algorithm": "Algo2", "use": "B", "value": 4.0},
        ]
        plot = ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="mark"))

        plot.create(rows=rows, xlabel="X", ylabel="Y", title="T", x="algorithm", y="value", hue="use", legend=True)

        axes = plt.gca()
        bands = [patch for patch in axes.patches if patch.get_hatch()]
        assert len(bands) == 1

        # Over the bar of Algo2/A, not over the whole Algo2 slot: the neighbouring bar of
        # Algo2/B keeps its own room.
        band = bands[0].get_window_extent()
        missing_bar = plot._slot_at(axes, ["Algo1", "Algo2"], ["A", "B"], "Algo2", "A")
        kept_bar = plot._slot_at(axes, ["Algo1", "Algo2"], ["A", "B"], "Algo2", "B")
        assert missing_bar is not None
        assert kept_bar is not None
        assert band.width < axes.get_window_extent().width / 2
        assert missing_bar[0] < kept_bar[0]

    def test_the_count_sits_under_the_group_it_belongs_to(self) -> None:
        """Test the number is placed per group, so two of them do not land on each other."""
        rows = [
            {"algorithm": "Algo1", "use": "A", "value": float("inf")},
            {"algorithm": "Algo1", "use": "B", "value": 2.0},
            {"algorithm": "Algo2", "use": "A", "value": float("nan")},
            {"algorithm": "Algo2", "use": "B", "value": 4.0},
        ]

        ConcreteBarPlot(figure=Figure(show=False), missing=Missing(policy="mark")).create(
            rows=rows, xlabel="X", ylabel="Y", title="T", x="algorithm", y="value", hue="use", legend=True
        )

        axes = plt.gca()
        assert sorted(text.get_text() for text in axes.texts) == ["1", "1"]
        # Anchored per group, so the two counts do not land on each other.
        assert len({cast("MatplotlibAnnotation", text).xy[0] for text in axes.texts}) == 2


class TestLegendPlacement:
    """Test where the key sits, whatever the plot has to explain."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    @staticmethod
    def _anchor(axes: Axes) -> tuple[float, float]:
        legend = axes.get_legend()
        assert legend is not None
        return tuple(legend.get_bbox_to_anchor().transformed(axes.transAxes.inverted()).bounds[:2])

    def test_an_ungrouped_legend_is_outside_the_axes(self) -> None:
        """Test even a lone error bar entry is kept off the data."""
        plot = ConcreteBarPlot(figure=Figure(show=False))

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 10.0}, {"algorithm": "Algo1", "value": 20.0}],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
            errorbar="sd",
        )

        assert self._anchor(plt.gca())[0] > 1.0

    def test_a_grouped_legend_is_outside_and_keeps_its_title(self) -> None:
        """Test the group legend still says what the groups are."""
        plot = ConcreteBarPlot(figure=Figure(show=False))

        plot.create(
            rows=[
                {"algorithm": "Algo1", "use": "A", "value": 10.0},
                {"algorithm": "Algo1", "use": "B", "value": 20.0},
            ],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
            hue="use",
            legend=True,
        )

        axes = plt.gca()
        assert self._anchor(axes)[0] > 1.0
        legend = axes.get_legend()
        assert legend is not None
        assert legend.get_title().get_text() == "use"

    def test_a_panel_of_a_shared_figure_keeps_its_key_inside(self) -> None:
        """Test the key of one panel is not drawn over the panel next to it.

        The room beside a panel belongs to its neighbour, so the rule that keeps a legend
        off the data would put this one on someone else's.
        """
        figure, panels = plt.subplots(1, 2)
        plot = ConcreteBarPlot(figure=Figure(show=False))
        plot._shared_axes = panels[0]
        plt.sca(panels[0])

        plot.create(
            rows=[{"algorithm": "Algo1", "value": 10.0}, {"algorithm": "Algo1", "value": 20.0}],
            xlabel="X",
            ylabel="Y",
            title="T",
            x="algorithm",
            y="value",
            errorbar="sd",
        )

        # In figure coordinates, since what it must not run into is the other panel.
        legend = panels[0].get_legend()
        assert legend is not None
        anchored = legend.get_bbox_to_anchor().transformed(figure.transFigure.inverted())
        assert anchored.x1 <= panels[0].get_window_extent().transformed(figure.transFigure.inverted()).x1
