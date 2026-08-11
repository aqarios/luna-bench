"""Luna colour palette and shared plot styling."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

_RGB_CHANNELS = 3

#: Colour of the horizontal reference lines. Black reads as an annotation of the axes
#: rather than as another series, which no brand colour manages next to coloured bars.
REFERENCE_LINE_COLOUR = "black"


class LunaColours(StrEnum):
    """Luna brand colours.

    The product colours form the default gradient ramp used by the plots,
    running ``LUNA_SOLVE`` (blue) -> ``LUNA_BENCH`` (sage) -> ``LUNA_Q`` (yellow).
    """

    LUNA_SOLVE = "#4773FF"  # blue,   hue 226
    LUNA_Q = "#ECC35B"  # yellow, hue  43
    LUNA_BENCH = "#79AE90"  # sage,   hue 146
    LUNA_MODEL = "#A855F7"  # purple, hue 271

    AQUA = "#102240"
    SKY = "#20252B"
    SAND = "#F1EDE5"
    MOON = "#A6A6A6"
    ROCKET_FIRE = "#D84141"

    # Backwards-compatible aliases of the product colours.
    AQARIOS = "#4773FF"
    STAR = "#ECC35B"
    SUCCESS = "#79AE90"

    @classmethod
    def ramp(cls) -> tuple[str, ...]:
        """Return the anchor colours of the default blue -> green -> yellow gradient."""
        return (str(cls.LUNA_SOLVE), str(cls.LUNA_BENCH), str(cls.LUNA_Q))

    @classmethod
    def palette(cls, num_colors: int = 6, *, anchors: Sequence[str] | None = None) -> list[str]:
        """Return *num_colors* colours along the Luna gradient, anchors included.

        The product colours are always part of the palette; only the shades between them
        are interpolated, so any number of categories gets a distinct colour without the
        brand colours dropping out of the figure.

        Parameters
        ----------
        num_colors : int, optional
            Number of colours to return, by default ``6``. Unlike a fixed list of
            brand colours this never runs out.
        anchors : Sequence[str] | None, optional
            Hex colours the gradient interpolates between, by default the Luna ramp
            (``LUNA_SOLVE`` -> ``LUNA_BENCH`` -> ``LUNA_Q``).

        Returns
        -------
        list[str]
            Hex colour strings, ordered from the first anchor to the last.
        """
        return gradient(anchors if anchors is not None else cls.ramp(), num_colors)


def gradient(anchors: Sequence[str], num_colors: int) -> list[str]:
    """Return *num_colors* colours along the gradient through *anchors*.

    The anchors themselves are always among them - the brand colours are the point of the
    palette, so a figure with four groups shows the blue, the sage and the yellow plus one
    blend, rather than four samples that happen to miss two of the three. Only the colours
    between them are interpolated, spread over the gaps as evenly as they divide.

    Fewer colours than anchors keeps the ends and drops from the middle, so two colours
    are the first and the last anchor rather than the first two.

    Parameters
    ----------
    anchors : Sequence[str]
        Hex colours (``"#RRGGBB"``) the gradient passes through, at least one.
    num_colors : int
        Number of colours to return. ``0`` or less yields an empty list.

    Returns
    -------
    list[str]
        Hex colour strings, ordered from the first anchor to the last.

    Raises
    ------
    ValueError
        If *anchors* is empty.
    """
    if not anchors:
        msg = "gradient() requires at least one anchor colour"
        raise ValueError(msg)

    if num_colors <= 0:
        return []

    stops = [_to_rgb(anchor) for anchor in anchors]

    if num_colors == 1 or len(stops) == 1:
        return [_to_hex(stops[0])] * num_colors

    if num_colors <= len(stops):
        picks = (round(index * (len(stops) - 1) / (num_colors - 1)) for index in range(num_colors))
        return [_to_hex(stops[pick]) for pick in picks]

    segments = len(stops) - 1
    between = num_colors - len(stops)
    # The remainder goes to the first gaps, so a palette that does not divide evenly is
    # denser at the blue end than at the yellow one rather than at an arbitrary gap.
    per_gap = [between // segments + (1 if gap < between % segments else 0) for gap in range(segments)]

    colors: list[str] = []
    for gap, count in enumerate(per_gap):
        colors.append(_to_hex(stops[gap]))
        colors.extend(_to_hex(_blend(stops[gap], stops[gap + 1], (step + 1) / (count + 1))) for step in range(count))
    colors.append(_to_hex(stops[-1]))

    return colors


def _blend(start: tuple[int, ...], end: tuple[int, ...], weight: float) -> tuple[int, ...]:
    """Return the colour *weight* of the way from *start* to *end*."""
    return tuple(round(s + (e - s) * weight) for s, e in zip(start, end, strict=True))


def _to_rgb(hex_colour: str) -> tuple[int, ...]:
    """Convert a ``"#RRGGBB"`` string into an ``(r, g, b)`` tuple."""
    value = str(hex_colour).lstrip("#")
    if len(value) != _RGB_CHANNELS * 2:
        msg = f"Expected a '#RRGGBB' colour, got {hex_colour!r}"
        raise ValueError(msg)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _to_hex(rgb: tuple[int, ...]) -> str:
    """Convert an ``(r, g, b)`` tuple into a ``"#RRGGBB"`` string."""
    return "#{:02X}{:02X}{:02X}".format(*rgb)


#: Deprecated alias kept for backwards compatibility; use :class:`LunaColours`.
AqariosColours = LunaColours

PALETTE = LunaColours.palette()
