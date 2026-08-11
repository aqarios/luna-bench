"""Tests for BarPlot generic class."""

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex
from matplotlib.patches import Rectangle

from luna_bench.custom import BaseFeature, FeatureResult, feature
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.dimensions import MetricDimension, ModelDimension
from luna_bench.plots.generics.bar_plot import BarPlot
from luna_bench.plots.plot_style import Annotation, ErrorBars, Figure
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

    @patch("luna_bench.plots.generics.bar_plot.check_optional_dependency")
    def test_create_adds_headroom_for_annotations(self, mock_check_dep: MagicMock) -> None:
        """Test annotated bars get extra room above the requested y limits."""
        _ = mock_check_dep
        with patch("seaborn.barplot"), patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.ylim") as mock_ylim:
            plot = ConcreteBarPlot(annotation=Annotation(headroom=0.5))
            rows = [{"algorithm": "Algo1", "value": 10}]

            plot.create(rows=rows, xlabel="X", ylabel="Y", title="Test", ylim=(0, 100))

            mock_ylim.assert_called_once_with(0, 150)

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
            def transform_rows(self, rows: list[dict[str, Any]], group_key: str | None) -> list[dict[str, Any]]:
                _ = group_key
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
