from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench.base_components import BasePlot


class PlotUserModel(BaseModel):
    name: str
    status: JobStatus

    plot: BasePlot  # type: ignore[type-arg]
