from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkStatus
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import SolveJobStorage
from .tables import (
    BenchmarkTable,
    PlotConfigTable,
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
    ) -> Result[None, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable(
                name=solve_job_name,
                status=BenchmarkStatus.CREATED,
                config_data=solve_job_config.model_dump_json(),
                benchmark=benchmark,
            )
            solve_job.save()
            return Success(None)
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
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
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_solvejob(
        benchmark_name: str, solve_job_name: str, solve_job_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        # TODO: delete results
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = PlotConfigTable.get(
                PlotConfigTable.name == solve_job_name, PlotConfigTable.benchmark == benchmark
            )
            solve_job.status = BenchmarkStatus.CREATED
            solve_job.config_data = solve_job_config.model_dump_json()
            solve_job.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_solvejob_status(
        benchmark_name: str, solve_job_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = PlotConfigTable.get(
                PlotConfigTable.name == solve_job_name, PlotConfigTable.benchmark == benchmark
            )
            solve_job.status = status
            solve_job.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result_solvejob(
        benchmark_name: str, solve_job_name: str, result: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solve_job_name, PlotConfigTable.benchmark == benchmark
            )
            result = SolveJobResultTable(
                solve_job=solve_job,
                result=result.model_dump_json(),
            )
            result.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result_solvejob(
        benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = SolveJobConfigTable.get(
                SolveJobConfigTable.name == solvejob_name, PlotConfigTable.benchmark == benchmark
            )
            result = SolveJobResultTable.get(SolveJobResultTable.solve_job == solve_job)
            result.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))
