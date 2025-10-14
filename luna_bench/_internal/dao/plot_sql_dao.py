from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError, ModelSelect
from returns.result import Failure, Success

from luna_bench._internal.domain_models import BenchmarkStatus, PlotDomain, RegisteredDataDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import PlotDao
from .tables import (
    BenchmarkTable,
    PlotConfigTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result

    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError


class PlotSqlDao(PlotDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def add(
        benchmark_name: str, plot_name: str, registered_id: str, plot_config: ArbitraryDataDomain
    ) -> Result[PlotDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.select(BenchmarkTable.id).where(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            plot = PlotConfigTable(
                name=plot_name,
                status=BenchmarkStatus.CREATED,
                config_data=plot_config,
                benchmark=benchmark,
                registered_id=registered_id,
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
            benchmark: ModelSelect = BenchmarkTable.select(BenchmarkTable.id).where(  # type: ignore[no-untyped-call]
                BenchmarkTable.name == benchmark_name
            )
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            plot.delete_instance(recursive=True)
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def update(
        benchmark_name: str, plot_name: str, registered_id: str, plot_config: ArbitraryDataDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark: ModelSelect = BenchmarkTable.select(BenchmarkTable.id).where(  # type: ignore[no-untyped-call]
                BenchmarkTable.name == benchmark_name
            )
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            plot.status = BenchmarkStatus.CREATED
            plot.config_data = plot_config
            plot.registered_id = registered_id
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
            benchmark: ModelSelect = BenchmarkTable.select(BenchmarkTable.id).where(  # type: ignore[no-untyped-call]
                BenchmarkTable.name == benchmark_name
            )
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            plot.status = status
            plot.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(benchmark_name: str, plot_name: str) -> Result[PlotDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark: ModelSelect = BenchmarkTable.select(BenchmarkTable.id).where(  # type: ignore[no-untyped-call]
                BenchmarkTable.name == benchmark_name
            )
            plot = PlotConfigTable.get(PlotConfigTable.name == plot_name, PlotConfigTable.benchmark == benchmark)  # type: ignore[no-untyped-call]
            return Success(PlotSqlDao.plot_to_domain(plot))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def plot_to_domain(plot: PlotConfigTable) -> PlotDomain:
        return PlotDomain(
            name=cast("str", plot.name),
            status=JobStatus(plot.status),
            config_data=RegisteredDataDomain(
                registered_id=cast("str", plot.registered_id),
                data=ArbitraryDataDomain.model_validate(plot.config_data, from_attributes=True),
            ),
        )
