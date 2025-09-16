from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from luna_bench._internal.domain_models import JobStatus, PlotConfigDomain


class Plot(BaseModel):
    name: str
    status: JobStatus

    model_config = ConfigDict(extra="allow")

    def run(self) -> None: ...

    def _to_domain_config(self) -> PlotConfigDomain.PlotConfig:
        return PlotConfigDomain.PlotConfig.model_validate_json(self.model_dump_json(exclude={"status", "name"}))

    @staticmethod
    def _from_domain(plot_config_domain: PlotConfigDomain) -> Plot:
        return Plot.model_validate(
            {
                "status": plot_config_domain.status,
                "name": plot_config_domain.name,
                **plot_config_domain.config_data.model_dump(),
            }
        )

    @staticmethod
    def _update(old_plot: Plot, new_plot: PlotConfigDomain) -> None:
        old_plot.name = new_plot.name
        old_plot.status = new_plot.status
        d = getattr(old_plot, "model_extra", None)
        if isinstance(d, dict):
            d.clear()

        old_plot.model_validate(new_plot.config_data.model_dump(exclude={"result"}))
