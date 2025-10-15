from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_quantum import Logging
from peewee import DoesNotExist, IntegrityError
from returns.result import Failure, Success

from luna_bench._internal.dao.algorithm_sql_dao import AlgorithmSqlDao
from luna_bench._internal.dao.feature_sql_dao import FeatureSqlDao
from luna_bench._internal.dao.metric_sql_dao import MetricSqlDao
from luna_bench._internal.domain_models import BenchmarkDomain, BenchmarkStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .modelset_sql_dao import ModelSetSqlDao
from .plot_sql_dao import PlotSqlDao
from .protocols import BenchmarkDao
from .tables import (
    BenchmarkTable,
    ModelSetTable,
)

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result


class BenchmarkSqlDao(BenchmarkDao):
    _logger: Logger = Logging.get_logger(__name__)

    @staticmethod
    def create(benchmark_name: str) -> Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]:
        benchmark = BenchmarkTable(name=benchmark_name, status=BenchmarkStatus.CREATED, modelset=None)
        try:
            benchmark.save()
            return Success(BenchmarkSqlDao.benchmark_to_domain(benchmark))
        except IntegrityError:
            return Failure(DataNotUniqueError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load(benchmark_name: str) -> Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            return Success(BenchmarkSqlDao.benchmark_to_domain(benchmark))
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def delete(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            benchmark.delete_instance()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def load_all() -> Result[list[BenchmarkDomain], UnknownLunaBenchError]:
        try:
            benchmarks = BenchmarkTable.select()  # type: ignore[no-untyped-call]
            return Success([BenchmarkSqlDao.benchmark_to_domain(b) for b in benchmarks])
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def set_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        try:
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            # TODO(Llewellyn): should this reset all results? # noqa: FIX002
            modelset = ModelSetTable.get(ModelSetTable.name == modelset_name)  # type: ignore[no-untyped-call]

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
            benchmark = BenchmarkTable.get(BenchmarkTable.name == benchmark_name)  # type: ignore[no-untyped-call]
            # TODO(Llewellyn): should this reset all results? # noqa: FIX002
            benchmark.modelset = None
            benchmark.save()
            return Success(None)
        except DoesNotExist:
            return Failure(DataNotExistError())
        except Exception as e:  # pragma: no cover
            return Failure(UnknownLunaBenchError(e))

    @staticmethod
    def benchmark_to_domain(benchmark: BenchmarkTable) -> BenchmarkDomain:
        return BenchmarkDomain(
            name=cast("str", benchmark.name),
            status=BenchmarkStatus(benchmark.status),
            modelset=ModelSetSqlDao.modelset_to_domain(benchmark.modelset) if benchmark.modelset else None,
            features=[FeatureSqlDao.feature_to_domain(feature) for feature in benchmark.features],
            algorithms=[AlgorithmSqlDao.solvejob_to_domain(solvejob) for solvejob in benchmark.algorithms],
            metrics=[MetricSqlDao.metric_to_domain(metric) for metric in benchmark.metrics],
            plots=[PlotSqlDao.plot_to_domain(plot) for plot in benchmark.plots],
        )
