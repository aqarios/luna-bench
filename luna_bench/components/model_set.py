from __future__ import annotations

from luna_quantum import Model
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from luna_bench._internal.entities.model_set.dao import ModelSetDAO
from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.shared.database.base_model import database


class ModelSet(BaseModel):
    class ModelData(BaseModel):
        model_id: int
        model_name: str
        model_hash: int

    id: int
    name: str
    models: list[ModelData]

    @staticmethod
    def create_dataset(dataset_name: str) -> ModelSet:
        result: Result[None, str] = ModelSetDAO.create_set(modelset_name=dataset_name)
        match result:
            case Success(value):
                print(f"Success: {value}")

                return ModelSet._to_data_set(value)
            case Failure(error):
                print(f"Error: {error}")
                raise RuntimeError(error)
            case _:
                # This should never be reached, but satisfies mypy
                raise RuntimeError("Unreachable code")

    # @staticmethod
    # def load_dataset(dataset_id: int) -> ModelSet:
    #     result: Result[ModelSetDomain, str] = ModelSetDAO.load_dataset(dataset_id=dataset_id)
    #     match result:
    #         case Success(value):
    #             print(f"Success: {value}")
    #             return ModelSet._to_data_set(value)
    #         case Failure(error):
    #             print(f"Error: {error}")
    #             raise RuntimeError(error)

    def add_model(self, model: Model) -> None:
        result = ModelSetDAO.create_model(model_name=model.name, model_hash=model.__hash__(), binary=model.encode())
        with database.atomic():
            match result:
                case Success(model):
                    r = ModelSetDAO.add_model_to_modelset(
                        modelset_id=self.id,
                        model_id=model.model_id,
                    )
                    match r:
                        case Success(model):
                            return
                        case Failure(error):
                            print(f"Error: {error}")
                            raise RuntimeError(error)
                        case _:
                            # This should never be reached, but satisfies mypy
                            raise RuntimeError("Unreachable code")
                case Failure(error):
                    print(f"Error: {error}")
                    raise RuntimeError(error)
                case _:
                    # This should never be reached, but satisfies mypy
                    raise RuntimeError("Unreachable code")

    @staticmethod
    def _to_model_data(model: ModelMetadataDomain) -> ModelData:
        print(model)
        return ModelData(model_name=model.name, model_hash=model.hash)

    @staticmethod
    def _to_data_set(dataset: ModelSetDomain) -> ModelSet:
        return ModelSet(
            id=dataset.modelset_id,
            name=dataset.name,
            models=[ModelSet._to_model_data(m) for m in dataset.models],
        )
