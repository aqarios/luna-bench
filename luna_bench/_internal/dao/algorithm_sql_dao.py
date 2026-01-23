from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import (
    AlgorithmDomain,
    AlgorithmResultDomain,
    BenchmarkStatus,
    RegisteredDataDomain,
)
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import AlgorithmDao
from .tables import (
    AlgorithmResultTable,
    AlgorithmTable,
    BenchmarkTable,
    ModelMetadataTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result

    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError


class AlgorithmSqlDao(AlgorithmDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str,
        algorithm_name: str,
        registered_id: str,
        algorithm_type: AlgorithmType,
        algorithm: ArbitraryDataDomain,
    ) -> Result[AlgorithmDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm_db = AlgorithmTable(
                name=algorithm_name,
                status=BenchmarkStatus.CREATED,
                algorithm_type=algorithm_type,
                benchmark=benchmark,
                config_data=algorithm,
                registered_id=registered_id,
            )
            algorithm_db.save()
            return Success(AlgorithmSqlDao.algorithm_to_domain(algorithm_db))
        except IntegrityError as e:
            return Failure(AlgorithmTable.map_integrity_error(e))
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, algorithm_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            algorithm.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str,
        algorithm_name: str,
        registered_id: str,
        algorithm_config: ArbitraryDataDomain,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        # TODO(Llewellyn): delete results  # noqa: FIX002
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            algorithm.status = BenchmarkStatus.CREATED
            algorithm.config_data = algorithm_config
            algorithm.registered_id = registered_id
            algorithm.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_status(
        benchmark_name: str, algorithm_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            algorithm.status = status
            algorithm.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(
        benchmark_name: str, algorithm_name: str
    ) -> Result[AlgorithmDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            AlgorithmSqlDao.algorithm_to_domain(algorithm)
            return Success(AlgorithmSqlDao.algorithm_to_domain(algorithm))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result(
        benchmark_name: str, algorithm_name: str, result: AlgorithmResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get_or_none(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]

            model_metadata = ModelMetadataTable.select(ModelMetadataTable.id).where(  # type: ignore[no-untyped-call]
                ModelMetadataTable.id == result.model_id
            )

            algorithm = AlgorithmTable.get_or_none(  # type: ignore[no-untyped-call]
                AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark
            )
            if algorithm is None:
                return Failure(DataNotExistError())

            existing_id = AlgorithmResultTable.get_or_none(  # type: ignore[no-untyped-call]
                (AlgorithmResultTable.algorithm == algorithm) & (AlgorithmResultTable.model_metadata == model_metadata)
            )

            algorithm_result = AlgorithmResultTable(
                id=existing_id,
                algorithm=algorithm,
                model_metadata=model_metadata,
                status=result.status,
                error=result.error,
                encoded_solution=result.solution_bytes,
                meta_data=result.meta_data,
                task_id=result.task_id,
                retrival_data=result.retrival_data,
            )
            algorithm_result.save()
            return Success(None)
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result(
        benchmark_name: str, algorithm_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            result = AlgorithmResultTable.get(AlgorithmResultTable.algorithm == algorithm)  # type: ignore[no-untyped-call]
            result.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def algorithm_to_domain(algorithm: AlgorithmTable) -> AlgorithmDomain:
        def to_domain(result: AlgorithmResultTable) -> AlgorithmResultDomain:
            to_return = AlgorithmResultDomain.model_construct(
                meta_data=result.meta_data,
                model_id=result.model_metadata.id,
                status=JobStatus(result.status),
                error=result.error,
                task_id=result.task_id,
                retrival_data=result.retrival_data,
            )

            to_return.solution = result.encoded_solution
            return to_return

        result_data: dict[str, AlgorithmResultDomain] = {
            r.model_metadata.name: to_domain(r) for r in list(algorithm.results)
        }

        return AlgorithmDomain(
            name=cast("str", algorithm.name),
            status=algorithm.status,
            algorithm_type=AlgorithmType(algorithm.algorithm_type),
            results=result_data,
            config_data=RegisteredDataDomain(
                registered_id=cast("str", algorithm.registered_id),
                data=ArbitraryDataDomain.model_validate(algorithm.config_data),
            ),
        )
