from __future__ import annotations

from pydantic import BaseModel

from luna_bench.custom import BasePlot
from luna_bench.custom.types import PlotName


class PlotEntity(BaseModel):
    """Represents a fully configured plot."""

    name: PlotName

    plot: BasePlot
