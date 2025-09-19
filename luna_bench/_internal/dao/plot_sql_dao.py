from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkStatus, PlotConfigDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import PlotDao
from .tables import (
    BenchmarkTable,
    PlotConfigTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result


class PlotSqlDao(PlotDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str, plot_name: str, plot_config: PlotConfigDomain.PlotConfig
    ) -> Result[PlotConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            plot = PlotConfigTable(
                name=plot_name,
                status=BenchmarkStatus.CREATED,
                config_data=plot_config,
                benchmark=benchmark,
            )
            plot.save()
            return Success(PlotSqlDao.plot_to_domain(plot))
        except IntegrityError as e:
            return Failure(PlotConfigTable.map_integrity_error(e))
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def remove(benchmark_name: str, plot_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)
            plot.delete_instance(recursive=True)
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str, plot_name: str, plot_config: PlotConfigDomain.PlotConfig
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)
            plot.status = BenchmarkStatus.CREATED
            plot.config_data = plot_config
            plot.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update_status(
        benchmark_name: str, plot_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)
            plot.status = status
            plot.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(
        benchmark_name: str, plot_name: str
    ) -> Result[PlotConfigDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)
            return Success(PlotSqlDao.plot_to_domain(plot))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def plot_to_domain(plot: PlotConfigTable) -> PlotConfigDomain:
        return PlotConfigDomain(
            id=plot.id,
            name=plot.name,
            status=plot.status,
            config_data=plot.config_data,
        )
