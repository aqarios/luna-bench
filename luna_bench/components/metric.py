from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from luna_bench._internal.domain_models import JobStatus, MetricConfigDomain


class Metric(BaseModel):
    name: str
    status: JobStatus

    model_config = ConfigDict(extra="allow")

    # results: list[MetricResults]

    def run(self) -> None: ...

    def result(self) -> None: ...

    def reset(self) -> None: ...

    def _to_domain_config(self) -> MetricConfigDomain.MetricConfig:
        return MetricConfigDomain.MetricConfig.model_validate_json(self.model_dump_json(exclude={"status", "name"}))

    @staticmethod
    def _from_domain(metric_config_domain: MetricConfigDomain) -> Metric:
        return Metric.model_validate(
            {
                "status": metric_config_domain.status,
                "name": metric_config_domain.name,
                **metric_config_domain.config_data.model_dump(),
            }
        )

    @staticmethod
    def _update(old_metric: Metric, new_metric: MetricConfigDomain) -> None:
        old_metric.name = new_metric.name
        old_metric.status = new_metric.status
        d = getattr(old_metric, "model_extra", None)
        if isinstance(d, dict):
            d.clear()

        old_metric.model_validate(new_metric.config_data.model_dump(exclude={"result"}))
