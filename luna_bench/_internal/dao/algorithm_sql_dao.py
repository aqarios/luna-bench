from __future__ import annotations

from typing import TYPE_CHECKING

from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import (
    AlgorithmDomain,
    AlgorithmResultDomain,
    RegisteredDataDomain,
)
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.logging import BenchLogger

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
    _logger: Logger = BenchLogger.get_logger(__name__)

    @staticmethod
    def add(  # noqa: PLR0913, PLR0917 # One argument per column of the row being written.
        benchmark_name: str,
        algorithm_name: str,
        registered_id: str,
        algorithm_type: AlgorithmType,
        algorithm: ArbitraryDataDomain,
        repetitions: int = 1,
    ) -> Result[AlgorithmDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            algorithm_db = AlgorithmTable(
                name=algorithm_name,
                algorithm_type=algorithm_type,
                benchmark=benchmark,
                config_data=algorithm,
                registered_id=registered_id,
                repetitions=repetitions,
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
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)
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
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)
            algorithm.config_data = algorithm_config
            algorithm.registered_id = registered_id
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
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)
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
            benchmark = BenchmarkTable.get_or_none(BenchmarkTable.name == benchmark_name)

            model_metadata = ModelMetadataTable.select(ModelMetadataTable.id).where(
                ModelMetadataTable.id == result.model_id
            )

            algorithm = AlgorithmTable.get_or_none(
                AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark
            )
            if algorithm is None:
                return Failure(DataNotExistError())

            # A run is identified by its repetition as well, so the two runs of the same
            # algorithm on the same model update their own row rather than each other's.
            existing_id = AlgorithmResultTable.get_or_none(
                (AlgorithmResultTable.algorithm == algorithm)
                & (AlgorithmResultTable.model_metadata == model_metadata)
                & (AlgorithmResultTable.repetition == result.repetition)
            )

            algorithm_result = AlgorithmResultTable(
                id=existing_id,
                algorithm=algorithm,
                model_metadata=model_metadata,
                repetition=result.repetition,
                status=result.status,
                error=result.error,
                encoded_solution=result.solution_bytes,
                meta_data=result.metadata_bytes,
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
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            algorithm = AlgorithmTable.get(AlgorithmTable.name == algorithm_name, AlgorithmTable.benchmark == benchmark)
            # peewee stubs leave `execute` untyped; `unused-ignore` keeps environments where mypy
            # does not flag the call (with `warn_unused_ignores`) passing as well.
            AlgorithmResultTable.delete().where(AlgorithmResultTable.algorithm == algorithm).execute()  # type: ignore[no-untyped-call, unused-ignore]
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def algorithm_to_domain(algorithm: AlgorithmTable) -> AlgorithmDomain:
        def to_domain(result: AlgorithmResultTable) -> AlgorithmResultDomain:
            to_return = AlgorithmResultDomain.model_construct(
                model_id=result.model_metadata.id,
                repetition=result.repetition,
                status=JobStatus(result.status),
                error=result.error,
                task_id=result.task_id,
                retrival_data=result.retrival_data,
            )

            to_return.solution = result.encoded_solution
            to_return.metadata_bytes = result.meta_data
            return to_return

        # Ordered by repetition rather than by row id, so the runs of a model read back in
        # the order they were asked for even when a reset left the table with gaps in it.
        result_data: dict[str, list[AlgorithmResultDomain]] = {}
        for r in sorted(algorithm.results, key=lambda r: r.repetition):
            result_data.setdefault(r.model_metadata.name, []).append(to_domain(r))

        return AlgorithmDomain(
            name=algorithm.name,
            algorithm_type=AlgorithmType(algorithm.algorithm_type),
            repetitions=algorithm.repetitions,
            results=result_data,
            config_data=RegisteredDataDomain(
                registered_id=algorithm.registered_id,
                data=ArbitraryDataDomain.model_validate(algorithm.config_data),
            ),
        )
