from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkStatus, MetricConfigDomain, MetricResultDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from ...errors.storage.data_not_unique_error import DataNotUniqueError
from .protocols import MetricDao
from .tables import (
    BenchmarkTable,
    MetricConfigTable,
    MetricResultTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from pydantic import BaseModel
    from returns.result import Result


class MetricSqlDao(MetricDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str, metric_name: str, metric_config: MetricConfigDomain.MetricConfig
    ) -> Result[MetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable(
                name=metric_name,
                status=BenchmarkStatus.CREATED,
                config_data=metric_config,
                benchmark=benchmark,
            )
            metric.status = BenchmarkStatus.CREATED
            metric.save()
            return Success(MetricSqlDao.metric_to_domain(metric))
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            metric.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str, metric_name: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )
            metric.status = BenchmarkStatus.CREATED
            metric.config_data = metric_config
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
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
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result(
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
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
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
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(
        benchmark_name: str, metric_name: str
    ) -> Result[MetricConfigDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            metric = MetricConfigTable.get(
                MetricConfigTable.name == metric_name, MetricConfigTable.benchmark == benchmark
            )

            return Success(MetricSqlDao.metric_to_domain(metric))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def metric_to_domain(metric: MetricConfigTable) -> MetricConfigDomain:
        result_data: MetricResultDomain | None = (
            MetricResultDomain.model_validate_json(metric.result.first().result_data) if metric.result.first() else None
        )

        return MetricConfigDomain(
            id=cast("int", metric.id),
            name=cast("str", metric.name),
            status=JobStatus(metric.status),
            config_data=metric.config_data,
            result=result_data,
        )
