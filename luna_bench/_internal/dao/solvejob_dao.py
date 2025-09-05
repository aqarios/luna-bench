from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkStatus, SolveJobConfigDomain, SolveJobResultDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import SolveJobStorage
from .tables import (
    BenchmarkTable,
    SolveJobConfigTable,
    SolveJobResultTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from pydantic import BaseModel
    from returns.result import Result


class SolveJobDAO(SolveJobStorage):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add_solvejob(
        benchmark_name: str, solve_job_name: str, solve_job_config: BaseModel
    ) -> Result[SolveJobConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable(
                name=solve_job_name,
                status=BenchmarkStatus.CREATED,
                config_data=solve_job_config.model_dump_json(),
                benchmark=benchmark,
            )
            solve_job.save()
            return Success(SolveJobDAO.solvejob_to_domain(solve_job))
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_solvejob(
        benchmark_name: str, solve_job_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solve_job_name, SolveJobConfigTable.benchmark == benchmark
            )
            solve_job.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_solvejob(
        benchmark_name: str, solve_job_name: str, solve_job_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        # TODO: delete results
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solve_job_name, SolveJobConfigTable.benchmark == benchmark
            )
            solve_job.status = BenchmarkStatus.CREATED
            solve_job.config_data = solve_job_config.model_dump_json()
            solve_job.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_solvejob_status(
        benchmark_name: str, solve_job_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solve_job_name, SolveJobConfigTable.benchmark == benchmark
            )
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
    ) -> Result[SolveJobConfigDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solvejob_name, SolveJobConfigTable.benchmark == benchmark
            )
            return Success(SolveJobDAO.solvejob_to_domain(solve_job))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result_solvejob(
        benchmark_name: str, solve_job_name: str, result: SolveJobResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solve_job_name, SolveJobConfigTable.benchmark == benchmark
            )
            result = SolveJobResultTable(
                solve_job=solve_job,
                meta_data=result.model_dump_json(),
                encoded_solution=result._solution_bytes,
            )
            result.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result_solvejob(
        benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solvejob_name, SolveJobConfigTable.benchmark == benchmark
            )
            result = SolveJobResultTable.get(SolveJobResultTable.solve_job == solve_job)
            result.delete_instance()
            return Success(None)
        except DoesNotExist:
            print("DOES NOT EXIST")
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def solvejob_to_domain(solvejob: SolveJobConfigTable) -> SolveJobConfigDomain:
        result_data: SolveJobResultDomain | None

        selected_data = solvejob.result.first()
        if selected_data:
            result_data = SolveJobResultDomain.model_validate_json(selected_data.meta_data)

            result_data._solution_bytes = selected_data.encoded_solution
        else:
            result_data = None

        return SolveJobConfigDomain(
            id=solvejob.id,
            name=solvejob.name,
            status=solvejob.status,
            config_data=SolveJobConfigDomain.SolveJobConfig.model_validate_json(solvejob.config_data),
            result=result_data,
        )
