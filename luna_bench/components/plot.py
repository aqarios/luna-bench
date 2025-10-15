from __future__ import annotations

from luna_bench._internal.user_models import PlotUserModel


class Plot(PlotUserModel):
    """User-facing plot class."""

    # TODO(Llewellyn): This can maybe be removed and PlotUserModel renamed to Plot.  # noqa: FIX002

    def run(self) -> None: ...  # noqa: D102 # Not yet implemented
