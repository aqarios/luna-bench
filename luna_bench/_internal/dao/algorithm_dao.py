from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from luna_quantum.solve.domain.abstract import LunaAlgorithm
from luna_quantum.solve.interfaces.algorithm_i import BACKEND_TYPE
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import AlgorithmConfigDomain, AlgorithmResultDomain, BenchmarkStatus
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import AlgorithmStorage
from .tables import (
    AlgorithmConfigTable,
    AlgorithmResultTable,
    BenchmarkTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result


class AlgorithmDAO(AlgorithmStorage):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str,
        solve_job_name: str,
        algorithm: AlgorithmConfigDomain.Algorithm,
        backend: AlgorithmConfigDomain.Backend | None = None,
    ) -> Result[AlgorithmConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable(
                name=solve_job_name,
                status=BenchmarkStatus.CREATED,
                benchmark=benchmark,
                algorithm=algorithm,
                backend=backend,
            )
            solve_job.save()
            return Success(AlgorithmDAO.solvejob_to_domain(solve_job))
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover

            print(e)
            print(e)
            print(e)
            print(e)
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, solve_job_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable.get(
                AlgorithmConfigTable.name == solve_job_name, AlgorithmConfigTable.benchmark == benchmark
            )
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
        algorithm: LunaAlgorithm[BACKEND_TYPE],
        backend: BACKEND_TYPE | None = None,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        # TODO: delete results
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable.get(
                AlgorithmConfigTable.name == solve_job_name, AlgorithmConfigTable.benchmark == benchmark
            )
            solve_job.status = BenchmarkStatus.CREATED
            solve_job.algorithm = algorithm
            solve_job.backend = backend
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
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable.get(
                AlgorithmConfigTable.name == solve_job_name, AlgorithmConfigTable.benchmark == benchmark
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
    ) -> Result[AlgorithmConfigDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable.get(
                AlgorithmConfigTable.name == solvejob_name, AlgorithmConfigTable.benchmark == benchmark
            )
            a = AlgorithmDAO.solvejob_to_domain(solve_job)
            return Success(AlgorithmDAO.solvejob_to_domain(solve_job))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_result(
        benchmark_name: str, solve_job_name: str, result_domain: AlgorithmResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable.get(
                AlgorithmConfigTable.name == solve_job_name, AlgorithmConfigTable.benchmark == benchmark
            )
            result = AlgorithmResultTable(
                solve_job=solve_job,
                meta_data=result_domain,
                encoded_solution=result_domain._solution_bytes,
                algorithm=solve_job,
            )
            result.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_result(
        benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            solve_job = AlgorithmConfigTable.get(
                AlgorithmConfigTable.name == solvejob_name, AlgorithmConfigTable.benchmark == benchmark
            )
            result = AlgorithmResultTable.get(AlgorithmResultTable.algorithm == solve_job)
            result.delete_instance()
            return Success(None)
        except DoesNotExist:
            print("DOES NOT EXIST")
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            print(e)
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def solvejob_to_domain(solvejob: AlgorithmConfigTable) -> AlgorithmConfigDomain:
        result_data: AlgorithmResultDomain | None

        selected_data = solvejob.result.first()
        if selected_data:
            result_data =AlgorithmResultDomain.model_validate(
                 selected_data.meta_data
            )

            result_data._solution_bytes = selected_data.encoded_solution
        else:
            result_data = None

        return AlgorithmConfigDomain(
            id=solvejob.id,
            name=solvejob.name,
            status=solvejob.status,
            algorithm=solvejob.algorithm,
            backend=solvejob.backend,
            result=result_data,
        )
