from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from ..domain_models import BenchmarkStatus, JobStatus, ModelmetricConfigDomain, ModelmetricResultDomain
from .protocols import ModelmetricStorage
from .tables import BenchmarkTable, ModelmetricConfigTable, ModelmetricResultTable

if TYPE_CHECKING:
    from logging import Logger


class ModelmetricDAO(ModelmetricStorage):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add_modelmetric(
        benchmark_name: str, modelmetric_name: str, modelmetric_config: ModelmetricConfigDomain.ModelmetricConfig
    ) -> Result[ModelmetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            modelmetric = ModelmetricConfigTable(
                name=modelmetric_name,
                status=BenchmarkStatus.CREATED,
                config_data=modelmetric_config,
                benchmark=benchmark,
            )
            modelmetric.status = BenchmarkStatus.CREATED
            modelmetric.save()
            return Success(ModelmetricDAO.modelmetric_to_domain(modelmetric))
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_modelmetric(
        benchmark_name: str, modelmetric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            modelmetric = ModelmetricConfigTable.get(
                ModelmetricConfigTable.name == modelmetric_name, ModelmetricConfigTable.benchmark == benchmark
            )
            modelmetric.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_modelmetric(
        benchmark_name: str, modelmetric_name: str, modelmetric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            modelmetric = ModelmetricConfigTable.get(
                ModelmetricConfigTable.name == modelmetric_name, ModelmetricConfigTable.benchmark == benchmark
            )
            modelmetric.status = BenchmarkStatus.CREATED
            modelmetric.config_data = modelmetric_config
            modelmetric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_modelmetric_status(
        benchmark_name: str, modelmetric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            modelmetric = ModelmetricConfigTable.get(
                ModelmetricConfigTable.name == modelmetric_name, ModelmetricConfigTable.benchmark == benchmark
            )
            modelmetric.status = status
            modelmetric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result_modelmetric(
        benchmark_name: str, modelmetric_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = ModelmetricConfigTable.get(
                ModelmetricConfigTable.name == modelmetric_name, ModelmetricConfigTable.benchmark == benchmark
            )

            result = ModelmetricResultTable(
                modelmetric=metric,
                result_data=result.model_dump_json(),
            )
            result.save()
            metric.status = BenchmarkStatus.DONE
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result_modelmetric(
        benchmark_name: str, modelmetric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = ModelmetricConfigTable.get(
                ModelmetricConfigTable.name == modelmetric_name, ModelmetricConfigTable.benchmark == benchmark
            )
            result = ModelmetricResultTable.get(ModelmetricResultTable.modelmetric == metric)
            result.delete_instance()
            metric.status = BenchmarkStatus.CREATED
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(
        benchmark_name: str, metric_name: str
    ) -> Result[ModelmetricConfigDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = ModelmetricConfigTable.get(
                ModelmetricConfigTable.name == metric_name, ModelmetricConfigTable.benchmark == benchmark
            )

            return Success(ModelmetricDAO.modelmetric_to_domain(metric))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def modelmetric_to_domain(modelmetric: ModelmetricConfigTable) -> ModelmetricConfigDomain:
        result_data: ModelmetricResultDomain | None = (
            ModelmetricResultDomain.model_validate_json(modelmetric.result.first().result_data)
            if modelmetric.result.first()
            else None
        )

        return ModelmetricConfigDomain(
            id=cast("int", modelmetric.id),
            name=cast("str", modelmetric.name),
            status=JobStatus(modelmetric.status),
            config_data=modelmetric.config_data,
            result=result_data,
        )
