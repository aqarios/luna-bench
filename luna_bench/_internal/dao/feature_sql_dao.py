from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Result, Success

from luna_bench._internal.dao.tables.model_metadata_table import ModelMetadataTable
from luna_bench._internal.domain_models import (
    BenchmarkStatus,
    FeatureDomain,
    FeatureResultDomain,
    RegisteredDataDomain,
)
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.entities.enums import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import FeatureDao
from .tables import BenchmarkTable, FeatureResultTable, FeatureTable

if TYPE_CHECKING:
    from logging import Logger

    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError


class FeatureSqlDao(FeatureDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str,
        feature_name: str,
        registered_id: str,
        feature_config: ArbitraryDataDomain,
    ) -> Result[FeatureDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            feature = FeatureTable(
                name=feature_name,
                status=BenchmarkStatus.CREATED,
                config_data=feature_config,
                benchmark=benchmark,
                registered_id=registered_id,
            )
            feature.save()
            return Success(FeatureSqlDao.feature_to_domain(feature))
        except IntegrityError as e:
            return Failure(FeatureTable.map_integrity_error(e))
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, feature_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            feature = FeatureTable.get(FeatureTable.name == feature_name, FeatureTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            feature.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str, feature_name: str, registered_id: str, feature_config: ArbitraryDataDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            feature = FeatureTable.get(FeatureTable.name == feature_name, FeatureTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            feature.status = BenchmarkStatus.CREATED
            feature.config_data = feature_config
            feature.registered_id = registered_id
            feature.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_status(
        benchmark_name: str, feature_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            feature = FeatureTable.get(FeatureTable.name == feature_name, FeatureTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            feature.status = status
            feature.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result(
        benchmark_name: str, feature_name: str, result: FeatureResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            model_metadata = ModelMetadataTable.select(ModelMetadataTable.id).where(  # type: ignore[no-untyped-call]
                ModelMetadataTable.name == result.model_name
            )
            feature = FeatureTable.get(FeatureTable.name == feature_name, FeatureTable.benchmark == benchmark)  # type: ignore[no-untyped-call]

            feature_result = FeatureResultTable(
                feature=feature,
                model_metadata=model_metadata,
                processing_time_ms=result.processing_time_ms,
                result_data=result.result,
                status=result.status.value,
                error=result.error,
            )
            feature_result.save()

            feature.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result(
        benchmark_name: str, feature_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            feature = FeatureTable.get(FeatureTable.name == feature_name, FeatureTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            result = FeatureResultTable.get(FeatureResultTable.feature == feature)  # type: ignore[no-untyped-call]
            result.delete_instance()
            feature.status = BenchmarkStatus.CREATED
            feature.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(
        benchmark_name: str, feature_name: str
    ) -> Result[FeatureDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            feature = FeatureTable.get(FeatureTable.name == feature_name, FeatureTable.benchmark == benchmark)  # type: ignore[no-untyped-call]

            return Success(FeatureSqlDao.feature_to_domain(feature))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def feature_to_domain(feature: FeatureTable) -> FeatureDomain:
        result_data: dict[str, FeatureResultDomain] = {
            f.model_metadata.name: FeatureResultDomain.model_construct(
                processing_time_ms=f.processing_time_ms,
                model_name=f.model_metadata.name,
                result=f.result_data,
                status=JobStatus(f.status),
                error=f.error,
            )
            for f in list(feature.results)
        }

        return FeatureDomain(
            name=cast("str", feature.name),
            status=JobStatus(feature.status),
            results=result_data,
            config_data=RegisteredDataDomain(
                registered_id=cast("str", feature.registered_id),
                data=ArbitraryDataDomain.model_validate(feature.config_data, from_attributes=True),
            ),
        )
