from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.dao.tables import AlgorithmTable
from luna_bench._internal.domain_models import BenchmarkStatus, MetricDomain, MetricResultDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import MetricDao
from .tables import (
    BenchmarkTable,
    MetricResultTable,
    MetricTable,
    ModelMetadataTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from pydantic import BaseModel
    from returns.result import Result

    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError


class MetricSqlDao(MetricDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str, metric_name: str, registered_id: str, metric_config: ArbitraryDataDomain
    ) -> Result[MetricDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable(
                name=metric_name,
                status=BenchmarkStatus.CREATED,
                config_data=metric_config,
                benchmark=benchmark,
                registered_id=registered_id,
            )
            metric.save()
            return Success(MetricSqlDao.metric_to_domain(metric))
        except IntegrityError as e:
            return Failure(MetricTable.map_integrity_error(e))
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            metric.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str, metric_name: str, registered_id: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            metric.status = BenchmarkStatus.CREATED
            metric.config_data = metric_config
            metric.registered_id = registered_id
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_status(
        benchmark_name: str, metric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            metric.status = status
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result(
        benchmark_name: str, metric_name: str, result: MetricResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            model_metadata = ModelMetadataTable.select(ModelMetadataTable.id).where(
                ModelMetadataTable.name == result.model_name
            )

            metric = MetricTable.get(  # type: ignore[no-untyped-call]
                MetricTable.name == metric_name, MetricTable.benchmark == benchmark
            )

            algorithm = AlgorithmTable.get(  # type: ignore[no-untyped-call]
                AlgorithmTable.name == result.algorithm_name, AlgorithmTable.benchmark == benchmark
            )
            metric_result = MetricResultTable(
                metric=metric,
                algorithm=algorithm,
                model_metadata=model_metadata,
                processing_time_ms=result.processing_time_ms,
                result_data=result.result,
                status=result.status.value,
                error=result.error,
            )
            metric_result.save()

            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            result = MetricResultTable.get(MetricResultTable.metric == metric)  # type: ignore[no-untyped-call]
            result.delete_instance()
            metric.status = BenchmarkStatus.CREATED
            metric.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(benchmark_name: str, metric_name: str) -> Result[MetricDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)  # type: ignore[no-untyped-call]

            return Success(MetricSqlDao.metric_to_domain(metric))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def metric_to_domain(metric: MetricTable) -> MetricDomain:
        result_data: dict[tuple[str, str], MetricResultDomain] = {
            (m.algorithm.name, m.model_metadata.name): MetricResultDomain.model_construct(
                processing_time_ms=m.processing_time_ms,
                model_name=m.model_metadata.name,
                algorithm_name=m.algorithm.name,
                result=m.result_data,
                status=JobStatus(m.status),
                error=m.error,
            )
            for m in list(metric.results)
        }

        return MetricDomain(
            name=cast("str", metric.name),
            status=JobStatus(cast("str", metric.status)),
            results=result_data,
            config_data=RegisteredDataDomain(
                registered_id=cast("str", metric.registered_id),
                data=ArbitraryDataDomain.model_validate(metric.config_data, from_attributes=True),
            ),
        )
