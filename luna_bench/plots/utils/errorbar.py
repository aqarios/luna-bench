"""Error bar configuration shared by the seaborn plots."""

from __future__ import annotations

from typing import Literal

#: Anything seaborn accepts for its ``errorbar`` parameter: a method name
#: (``"sd"``, ``"se"``, ``"ci"``, ``"pi"``), a ``(method, level)`` pair, or ``None``.
type ErrorBar = str | tuple[str, float] | None

#: Sentinel meaning "derive the error bar from the aggregation".
AUTO_ERRORBAR: Literal["auto"] = "auto"

_SPREAD_LABELS = {"sd": "SD", "se": "SE"}
_INTERVAL_LABELS = {"ci": "CI", "pi": "PI"}
_DEFAULT_INTERVAL_LEVEL = 95.0


def errorbar_label(errorbar: ErrorBar) -> str:
    """Return a legend label describing *errorbar*.

    Parameters
    ----------
    errorbar : ErrorBar
        Seaborn error bar specification, e.g. ``"sd"``, ``("ci", 95)``.

    Returns
    -------
    str
        Human-readable label such as ``"± 1 SD"`` or ``"95% CI"``. Unknown
        specifications fall back to their own string representation.
    """
    method, level = (errorbar[0], errorbar[1]) if isinstance(errorbar, tuple) else (errorbar, None)

    if method in _SPREAD_LABELS:
        return f"± {level if level is not None else 1:g} {_SPREAD_LABELS[method]}"

    if method in _INTERVAL_LABELS:
        return f"{level if level is not None else _DEFAULT_INTERVAL_LEVEL:g}% {_INTERVAL_LABELS[method]}"

    return str(errorbar)
