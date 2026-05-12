from __future__ import annotations

from pydantic import BaseModel

from luna_bench.base_components import BasePlot
from luna_bench.types import PlotName

from .enums import JobStatus


class PlotEntity(BaseModel):
    """Represents a fully configured plot."""

    name: PlotName
    status: JobStatus

    plot: BasePlot
