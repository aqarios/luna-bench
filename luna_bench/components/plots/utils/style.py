"""Luna colour palette and shared plot styling."""

from __future__ import annotations

from enum import StrEnum


class AqariosColours(StrEnum):
    """Luna brand colours."""

    AQUA = "#102240"
    AQARIOS = "#4773FF"
    SKY = "#20252B"
    SAND = "#F1EDE5"
    MOON = "#A6A6A6"
    SUCCESS = "#79AE90"
    ROCKET_FIRE = "#D84141"
    STAR = "#ECC35B"

    @classmethod
    def palette(cls, num_colors: int = 6) -> list[str]:
        """Return the first *num_colors* colours from the Luna palette.

        Parameters
        ----------
        num_colors:
            Number of colours to include (max 6). Defaults to 6.
        """
        default = [cls.AQARIOS, cls.SUCCESS, cls.STAR, cls.ROCKET_FIRE, cls.MOON, cls.AQUA]
        return [str(c) for c in default[:num_colors]]


PALETTE = AqariosColours.palette()
