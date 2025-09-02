from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkDomain, BenchmarkStatus, ModelSetDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .modelset_dao import ModelSetDAO
from .plot_dao import PlotDAO
from .protocols import BenchmarkStorage
from .tables import (
    BenchmarkTable,
    ModelSetTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result


class BenchmarkDAO(BenchmarkStorage):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def create(benchmark_name: str) -> Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]:
        benchmark = BenchmarkTable(name=benchmark_name, status=BenchmarkStatus.CREATED, modelset=None)
        try:
            benchmark.save()
            return Success(BenchmarkDAO.benchmark_to_domain(benchmark))
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(benchmark_name: str) -> Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            return Success(BenchmarkDAO.benchmark_to_domain(benchmark))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def delete(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            benchmark.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load_all() -> Result[list[BenchmarkDomain], UnknownLunaBenchError]:
        try:
            benchmarks = BenchmarkTable.select()
            return Success([BenchmarkDAO.benchmark_to_domain(b) for b in benchmarks])
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            # TODO: should this reset all results?
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)

            benchmark.modelset = modelset
            benchmark.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove_modelset(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            # TODO: should this reset all results?
            benchmark.modelset = None
            benchmark.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)
            benchmark.modelset = modelset
            benchmark.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def benchmark_to_domain(benchmark: BenchmarkTable) -> BenchmarkDomain:
        modelset: ModelSetTable | None = benchmark.modelset

        models_set_domain: ModelSetDomain | None = None
        if modelset:
            models_set_domain = ModelSetDAO.modelset_to_domain(modelset)

        return BenchmarkDomain(
            id=benchmark.id,
            name=benchmark.name,
            status=benchmark.status,
            modelset=models_set_domain,
            modelmetrics=[],
            solve_jobs=[],
            metrics=[],
            plots=[PlotDAO.plot_to_domain(plot) for plot in benchmark.plots],
        )
