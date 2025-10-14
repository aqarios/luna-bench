from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.interfaces.plot_i import IPlot


class PlotUserModel(BaseModel):
    name: str
    status: JobStatus

    plot: IPlot
