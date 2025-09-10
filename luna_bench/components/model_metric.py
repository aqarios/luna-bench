from __future__ import annotations

from dependency_injector.wiring import inject
from luna_quantum.client.schemas.enums.status import StatusEnum
from pydantic import BaseModel, ConfigDict

from luna_bench._internal.domain_models import ModelmetricConfigDomain


class ModelMetric(BaseModel):
    name: str
    status: StatusEnum

    model_config = ConfigDict(extra="allow")


    def run(self) -> None: ...

    def result(self) -> None: ...

    def reset(self) -> None: ...



    def _to_domain_config(self)-> ModelmetricConfigDomain.ModelmetricConfig:
        return ModelmetricConfigDomain.ModelmetricConfig.model_validate_json(self.model_dump_json(exclude={"status", "name"}))
        

    @staticmethod
    def _from_domain(modelmetric_config_domain: ModelmetricConfigDomain) -> ModelMetric:
        return ModelMetric.model_validate(
            {
            "status":modelmetric_config_domain.status,
            "name":modelmetric_config_domain.name,
            **modelmetric_config_domain.config_data.model_dump()})


    @staticmethod
    def _update(old_modelmetric: ModelMetric, new_modelmetric: ModelmetricConfigDomain)-> None:
        old_modelmetric.name = new_modelmetric.name
        old_modelmetric.status = new_modelmetric.status
        d = getattr(old_modelmetric, "model_extra", None)
        if isinstance(d, dict):
            d.clear()

        old_modelmetric.model_validate(new_modelmetric.config_data.model_dump(exclude={"result"}))