"""Tests for the option bundles a plot can be configured with."""

import pytest

from luna_bench.custom import BaseFeature, FeatureResult, feature
from luna_bench.features import VarNumberFeature
from luna_bench.plots import (
    Annotation,
    ErrorBars,
    FeasibleSolutionFoundPlot,
    Figure,
    PlotStyle,
    RuntimePlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.plots.dimensions import FeatureDimension, ModelDimension
from luna_bench.plots.utils import Aggregation, LunaColours


@feature
class RegisteredGroupFeature(BaseFeature[FeatureResult]):
    """A registered feature, so a stored grouping id can be resolved back to it."""

    def run(self, model: object) -> FeatureResult:
        """Unused; the grouping only ever names the class."""
        raise NotImplementedError


class TestOptions:
    """Test what a bundle hands to a plot."""

    def test_only_what_was_given_is_handed_on(self) -> None:
        """Test an option the bundle does not mention is left at the plot's default."""
        assert Figure(width=12).given() == {"width": 12}

    def test_only_the_given_fields_are_reported(self) -> None:
        """Test a bundle knows what it was told, so merging it overrides only that."""
        assert Annotation(fontsize=7, max_decimals=6).given() == {"max_decimals": 6, "fontsize": 7}
        assert ErrorBars(spec=None, capsize=0.0).given() == {"spec": None, "capsize": 0.0}

    def test_a_style_carries_the_bundles_it_holds(self) -> None:
        """Test one style can carry the whole look of a benchmark."""
        style = PlotStyle(
            figure=Figure(width=12, show=False),
            annotation=Annotation(fontsize=7),
            aggregation=Aggregation.MAX,
        )

        assert style.given() == {
            "figure": Figure(width=12, show=False),
            "annotation": Annotation(fontsize=7),
            "aggregation": Aggregation.MAX,
        }

    def test_a_bundle_rejects_an_unknown_option(self) -> None:
        """Test a typo is reported rather than silently ignored."""
        with pytest.raises(ValueError, match="fontsizes"):
            Annotation(fontsizes=7)  # type: ignore[call-arg]

    def test_file_formats_accepts_a_single_format(self) -> None:
        """Test the bundle takes the same shorthand as the plot."""
        assert Figure(file_formats="pgf").given() == {"file_formats": ("pgf",)}  # type: ignore[arg-type]


class TestPlotsTakeBundles:
    """Test that a plot can be configured by concern instead of by keyword."""

    def test_a_bundle_sets_the_options_it_carries(self) -> None:
        """Test the options arrive on the plot under their own names."""
        plot = RuntimePlot(
            figure=Figure(width=12, dpi=200, show=False),
            annotation=Annotation(fontsize=7, max_decimals=6),
            grouping=FeatureDimension(feature=VarNumberFeature, label="Size"),
            errorbars=ErrorBars(capsize=0.0),
        )

        assert (plot.figure.width, plot.figure.dpi, plot.figure.show) == (12, 200, False)
        assert plot.annotation is not None
        assert (plot.annotation.fontsize, plot.annotation.max_decimals) == (7, 6)
        assert plot.grouping == FeatureDimension(feature=VarNumberFeature, label="Size")
        assert plot.errorbars is not None
        assert plot.errorbars.capsize == 0.0

    def test_untouched_options_keep_the_plot_default(self) -> None:
        """Test configuring one concern does not reset the others."""
        plot = RuntimePlot(figure=Figure(width=12))

        assert plot.figure.height == 6
        assert plot.errorbars is not None
        assert plot.errorbars.color == LunaColours.SKY
        assert plot.figure.title == "Runtime per Solver"

    def test_a_flat_option_wins_over_a_bundle(self) -> None:
        """Test the name an option had before the bundles still works, and is the most specific."""
        plot = RuntimePlot(figure=Figure(width=12, dpi=200), width=6)  # type: ignore[call-arg]

        assert (plot.figure.width, plot.figure.dpi) == (6, 200)

    def test_a_bundle_wins_over_the_shared_style(self) -> None:
        """Test one plot can differ from the look the benchmark shares."""
        style = PlotStyle(figure=Figure(width=12, show=False), annotation=Annotation(fontsize=7))

        plot = RuntimePlot(style=style, annotation=Annotation(rotation=90))

        assert (plot.figure.width, plot.figure.show) == (12, False)
        assert plot.annotation is not None
        assert plot.annotation.rotation == 90
        # Option by option, not bundle by bundle: what the plot's Annotation does not
        # mention is still the style's.
        assert plot.annotation is not None
        assert plot.annotation.fontsize == 7

    def test_no_annotation_at_all_wins_over_the_shared_style(self) -> None:
        """Test a plot with too many bars to label says so with None, not with a flag."""
        style = PlotStyle(annotation=Annotation(fontsize=7))

        assert RuntimePlot(style=style, annotation=None).annotation is None

    def test_a_style_can_be_shared_between_plots(self) -> None:
        """Test the same style object configures any number of plots."""
        style = PlotStyle(figure=Figure(width=12, show=False))

        assert RuntimePlot(style=style).figure.width == 12
        assert RuntimePlot(style=style, figure=Figure(title="Other")).figure.width == 12

    def test_options_a_plot_does_not_have_are_ignored(self) -> None:
        """Test one style can be spread over bar plots and scatter plots alike."""
        style = PlotStyle(figure=Figure(width=12), annotation=Annotation(fontsize=7))

        plot = RuntimeVsVarNumberPlot(style=style)

        assert plot.figure.width == 12
        assert not hasattr(plot, "annotation")

    def test_a_wrong_bundle_is_reported(self) -> None:
        """Test the argument names which bundle it takes."""
        with pytest.raises(TypeError, match="'annotation' takes a Annotation, got ModelDimension"):
            RuntimePlot(annotation=ModelDimension())  # type: ignore[arg-type]

    def test_the_flat_names_still_configure_a_plot(self) -> None:
        """Test code and stored configurations written before the bundles keep working."""
        plot = RuntimePlot(width=12, annotate_fontsize=7, group_by="model", errorbar_capsize=0.0)  # type: ignore[call-arg]

        assert plot.annotation is not None
        assert plot.figure.width == 12
        assert plot.annotation.fontsize == 7
        assert plot.grouping == ModelDimension()
        assert plot.errorbars is not None
        assert plot.errorbars.capsize == 0.0

    def test_the_flat_annotate_flag_turns_them_off(self) -> None:
        """Test what used to be a flag inside the options is now not having any."""
        assert RuntimePlot(annotate=False).annotation is None  # type: ignore[call-arg]

    def test_a_subclass_default_survives_a_bundle(self) -> None:
        """Test configuring one option does not reset what the plot declares itself."""
        plot = FeasibleSolutionFoundPlot(annotation=Annotation(fontsize=7))

        assert plot.annotation is not None
        assert plot.annotation.fontsize == 7
        assert plot.annotation.format == "{:.1f}%"


class TestInstalledStyle:
    """Test the style a whole benchmark is drawn in."""

    def teardown_method(self) -> None:
        """Leave no style installed for the next test."""
        PlotStyle.clear()

    def test_a_plot_starts_from_the_installed_style(self) -> None:
        """Test one look does not have to be handed to every plot."""
        PlotStyle(figure=Figure(width=12, show=False), annotation=Annotation(fontsize=7)).use()

        plot = RuntimePlot()

        assert (plot.figure.width, plot.figure.show) == (12, False)
        assert plot.annotation is not None
        assert plot.annotation.fontsize == 7

    def test_a_plot_still_wins_over_it(self) -> None:
        """Test installing a style sets the starting point, not the outcome."""
        PlotStyle(figure=Figure(width=12, show=False)).use()

        plot = RuntimePlot(figure=Figure(width=8))

        assert (plot.figure.width, plot.figure.show) == (8, False)

    def test_a_style_given_to_a_plot_merges_over_the_installed_one(self) -> None:
        """Test the two styles combine option by option, not bundle by bundle."""
        PlotStyle(figure=Figure(width=12, show=False)).use()

        plot = RuntimePlot(style=PlotStyle(figure=Figure(dpi=200)))

        assert (plot.figure.width, plot.figure.dpi, plot.figure.show) == (12, 200, False)

    def test_it_applies_to_the_plots_built_after_it(self) -> None:
        """Test a plot holds what it was built with, whatever is installed later."""
        before = RuntimePlot()

        PlotStyle(figure=Figure(width=12)).use()

        assert before.figure.width == 8
        assert RuntimePlot().figure.width == 12

    def test_it_can_be_installed_for_one_block_only(self) -> None:
        """Test the style can be put back, which is what a test or a report section wants."""
        with PlotStyle(figure=Figure(width=12)).use():
            assert RuntimePlot().figure.width == 12

        assert PlotStyle.installed() is None
        assert RuntimePlot().figure.width == 8

    def test_nothing_is_installed_by_default(self) -> None:
        """Test a plot is its own default until a style says otherwise."""
        assert PlotStyle.installed() is None
