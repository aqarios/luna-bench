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
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import AlgorithmDao
from .tables import (
    AlgorithmResultTable,
    AlgorithmTable,
    BenchmarkTable,
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
        solve_job_name: str,
        registered_id: str,
        algorithm: ArbitraryDataDomain,
    ) -> Result[AlgorithmDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            algorithm_db = AlgorithmTable(
                name=solve_job_name,
                status=BenchmarkStatus.CREATED,
                benchmark=benchmark,
                config_data=algorithm,
                registered_id=registered_id,
            )
            algorithm_db.save()
            return Success(AlgorithmSqlDao.solvejob_to_domain(algorithm_db))
        except IntegrityError as e:
            return Failure(AlgorithmTable.map_integrity_error(e))
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, solve_job_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            solve_job = AlgorithmTable.get(AlgorithmTable.name == solve_job_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            solve_job.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str,
        solve_job_name: str,
        registered_id: str,
        algorithm: ArbitraryDataDomain,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        # TODO(Llewellyn): delete results  # noqa: FIX002
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            solve_job = AlgorithmTable.get(AlgorithmTable.name == solve_job_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            solve_job.status = BenchmarkStatus.CREATED
            solve_job.config_data = algorithm
            solve_job.registered_id = registered_id
            solve_job.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_status(
        benchmark_name: str, solve_job_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            solve_job = AlgorithmTable.get(AlgorithmTable.name == solve_job_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            solve_job.status = status
            solve_job.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(
        benchmark_name: str, solvejob_name: str
    ) -> Result[AlgorithmDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            solve_job = AlgorithmTable.get(AlgorithmTable.name == solvejob_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            AlgorithmSqlDao.solvejob_to_domain(solve_job)
            return Success(AlgorithmSqlDao.solvejob_to_domain(solve_job))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result(
        benchmark_name: str, solve_job_name: str, result_domain: AlgorithmResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            solve_job = AlgorithmTable.get(AlgorithmTable.name == solve_job_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]

            result = AlgorithmResultTable(
                solve_job=solve_job,
                meta_data=result_domain.meta_data,
                encoded_solution=result_domain.solution_bytes,
                algorithm=solve_job,
            )
            result.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result(
        benchmark_name: str, solve_job_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            solve_job = AlgorithmTable.get(AlgorithmTable.name == solve_job_name, AlgorithmTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            result = AlgorithmResultTable.get(AlgorithmResultTable.algorithm == solve_job)  # type: ignore[no-untyped-call]
            result.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def solvejob_to_domain(solve_job: AlgorithmTable) -> AlgorithmDomain:
        result_data: AlgorithmResultDomain | None

        selected_data = solve_job.result.first()
        if selected_data:
            result_data = AlgorithmResultDomain(meta_data=selected_data.meta_data)

            result_data.solution_bytes = selected_data.encoded_solution
        else:
            result_data = None

        return AlgorithmDomain(
            name=cast("str", solve_job.name),
            status=JobStatus(solve_job.status),
            result=result_data,
            config_data=RegisteredDataDomain(
                registered_id=cast("str", solve_job.registered_id),
                data=ArbitraryDataDomain.model_validate(solve_job.config_data),
            ),
        )
