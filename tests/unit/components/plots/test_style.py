"""Tests for the Luna palette."""

import pytest

from luna_bench.plots.utils.errorbar import ErrorBar, errorbar_label
from luna_bench.plots.utils.style import LunaColours, gradient

BLUE, SAGE, YELLOW = LunaColours.ramp()


class TestPalette:
    """Test the colours a plot spreads over its groups."""

    @pytest.mark.parametrize("num_colors", range(3, 13))
    def test_the_brand_colours_are_always_part_of_it(self, num_colors: int) -> None:
        """Test the point of the palette does not drop out of a figure with four groups."""
        palette = LunaColours.palette(num_colors)

        assert len(palette) == num_colors
        assert set(LunaColours.ramp()) <= set(palette)

    def test_it_runs_from_the_first_anchor_to_the_last(self) -> None:
        """Test the order is the ramp's, so the gradient reads left to right."""
        palette = LunaColours.palette(7)

        assert palette[0] == BLUE
        assert palette[-1] == YELLOW
        assert palette.index(SAGE) == 3

    def test_the_shades_between_are_interpolated(self) -> None:
        """Test what is not an anchor lies between the two it sits between."""
        palette = LunaColours.palette(5)

        assert palette == [BLUE, "#6090C8", SAGE, "#B2B876", YELLOW]

    @pytest.mark.parametrize(("num_colors", "expected"), [(1, [BLUE]), (2, [BLUE, YELLOW])])
    def test_fewer_colours_than_anchors_keeps_the_ends(self, num_colors: int, expected: list[str]) -> None:
        """Test two colours are the ends of the ramp, not its first two anchors."""
        assert LunaColours.palette(num_colors) == expected

    def test_no_colours_at_all(self) -> None:
        """Test a plot with nothing to colour asks for nothing."""
        assert LunaColours.palette(0) == []

    def test_a_single_anchor_repeats(self) -> None:
        """Test a gradient needs two colours to be a gradient."""
        assert gradient([BLUE], 3) == [BLUE, BLUE, BLUE]

    def test_a_custom_ramp_keeps_its_own_anchors(self) -> None:
        """Test the guarantee is about the anchors given, not about the Luna ones."""
        anchors = [BLUE, LunaColours.ROCKET_FIRE]

        palette = gradient(anchors, 4)

        assert palette[0] == BLUE
        assert palette[-1] == LunaColours.ROCKET_FIRE
        assert len(palette) == 4

    def test_an_empty_ramp_is_rejected(self) -> None:
        """Test a gradient through nothing is a mistake, not an empty palette."""
        with pytest.raises(ValueError, match="at least one anchor"):
            gradient([], 3)


class TestColourParsing:
    """Test the colours a gradient is built from."""

    def test_a_colour_that_is_not_a_hex_triple_is_rejected(self) -> None:
        """Test a mistyped anchor is reported rather than drawn as something else."""
        with pytest.raises(ValueError, match="Expected a '#RRGGBB' colour"):
            gradient(["#4773F", "#ECC35B"], 3)


class TestErrorBarLabel:
    """Test how an error bar names itself in the legend."""

    @pytest.mark.parametrize(
        ("errorbar", "expected"),
        [("sd", "± 1 SD"), ("se", "± 1 SE"), (("ci", 95), "95% CI"), ("ci", "95% CI"), (("pi", 50), "50% PI")],
    )
    def test_the_known_specifications_read_as_words(self, errorbar: ErrorBar, expected: str) -> None:
        """Test the legend says what the bar shows rather than repeating seaborn's spelling."""
        assert errorbar_label(errorbar) == expected

    def test_anything_else_says_what_it_was_given(self) -> None:
        """Test a specification only seaborn knows still labels its bar."""
        assert errorbar_label("mystery") == "mystery"
