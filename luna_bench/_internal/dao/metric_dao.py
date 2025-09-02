from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import DoesNotExist
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkStatus
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import MetricStorage
from .tables import (
    BenchmarkTable,
    MetricConfigTable,
    MetricResultTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from pydantic import BaseModel
    from returns.result import Result


class MetricDAO(MetricStorage):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add_metric(
        benchmark_name: str, metric_name: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable(
                name=metric_name,
                status=BenchmarkStatus.CREATED,
                config_data=metric_config.model_dump_json(),
                benchmark=benchmark,
            )
            metric.status = BenchmarkStatus.CREATED
            metric.config_data = metric_config.model_dump_json()
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_metric(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            metric.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_metric(
        benchmark_name: str, metric_name: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            metric.status = BenchmarkStatus.CREATED
            metric.config_data = metric_config.model_dump_json()
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_metric_status(
        benchmark_name: str, metric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            metric.status = status
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result_metric(
        benchmark_name: str, metric_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            result = MetricResultTable(
                metric=metric,
                result_data=result.model_dump_json(),
            )
            result.save()
            metric.status = BenchmarkStatus.DONE
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result_metric(
        benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            result = MetricResultTable.get(MetricResultTable.metric == metric)
            result.delete_instance()
            metric.status = BenchmarkStatus.CREATED
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))
