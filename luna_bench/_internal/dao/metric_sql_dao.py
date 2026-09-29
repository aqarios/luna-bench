from __future__ import annotations

from typing import TYPE_CHECKING

from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.dao.tables import AlgorithmTable
from luna_bench._internal.domain_models import MetricDomain, MetricResultDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.logging import BenchLogger

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

    from luna_bench.custom.types import AlgorithmName, ModelName
    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError


class MetricSqlDao(MetricDao):
    _logger: Logger = BenchLogger.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str, metric_name: str, registered_id: str, metric_config: ArbitraryDataDomain
    ) -> Result[MetricDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable(
                name=metric_name,
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
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)
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
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)
            metric.config_data = metric_config
            metric.registered_id = registered_id
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

            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)

            algorithm = AlgorithmTable.get(
                AlgorithmTable.name == result.algorithm_name, AlgorithmTable.benchmark == benchmark
            )
            # Upsert, as the algorithm results are written: a metric that failed on one
            # run and is computed again replaces that row instead of colliding with it on
            # the unique index over (model, metric, algorithm, repetition).
            existing_id = MetricResultTable.get_or_none(
                (MetricResultTable.metric == metric)
                & (MetricResultTable.algorithm == algorithm)
                & (MetricResultTable.model_metadata == model_metadata)
                & (MetricResultTable.repetition == result.repetition)
            )

            metric_result = MetricResultTable(
                id=existing_id,
                metric=metric,
                algorithm=algorithm,
                model_metadata=model_metadata,
                repetition=result.repetition,
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
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)
            # peewee stubs leave `execute` untyped; `unused-ignore` keeps environments where mypy
            # does not flag the call (with `warn_unused_ignores`) passing as well.
            MetricResultTable.delete().where(MetricResultTable.metric == metric).execute()  # type: ignore[no-untyped-call, unused-ignore]
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(benchmark_name: str, metric_name: str) -> Result[MetricDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            metric = MetricTable.get(MetricTable.name == metric_name, MetricTable.benchmark == benchmark)

            return Success(MetricSqlDao.metric_to_domain(metric))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def metric_to_domain(metric: MetricTable) -> MetricDomain:
        # One entry per repetition of the algorithm, ordered by it, so a caller reading
        # results[model][algorithm] gets the runs in the order they were made.
        result_data: dict[ModelName, dict[AlgorithmName, list[MetricResultDomain]]] = {}
        for m in sorted(metric.results, key=lambda m: m.repetition):
            result_data.setdefault(m.model_metadata.name, {}).setdefault(m.algorithm.name, []).append(
                MetricResultDomain.model_construct(
                    processing_time_ms=m.processing_time_ms,
                    model_name=m.model_metadata.name,
                    algorithm_name=m.algorithm.name,
                    repetition=m.repetition,
                    result=m.result_data,
                    status=JobStatus(m.status),
                    error=m.error,
                )
            )

        return MetricDomain(
            name=metric.name,
            results=result_data,
            config_data=RegisteredDataDomain(
                registered_id=metric.registered_id,
                data=ArbitraryDataDomain.model_validate(metric.config_data, from_attributes=True),
            ),
        )
