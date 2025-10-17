from dependency_injector.wiring import Provide, inject
from pydantic import ValidationError
from returns.result import Result

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import BenchmarkDomain
from luna_bench._internal.mappers.container import MapperContainer
from luna_bench._internal.mappers.types import Mapper
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkCreateUc


class BenchmarkCreateUcImpl(BenchmarkCreateUc):
    _transaction: DaoTransaction
    _benchmark_mapper: Mapper[BenchmarkDomain, BenchmarkUserModel]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        benchmark_mapper: Mapper[BenchmarkDomain, BenchmarkUserModel] = Provide[MapperContainer.benchmark_mapper],
    ) -> None:
        """
        Initialize the BenchmarkCreateImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        benchmark_mapper: Mapper[BenchmarkDomain, BenchmarkUserModel]
            Benchmark mapper.
        """
        self._transaction = transaction
        self._benchmark_mapper = benchmark_mapper

    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError]:
        with self._transaction as t:
            result_dao: Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError] = t.benchmark.create(
                benchmark_name
            )
            return self._benchmark_mapper.return_to_user_model(
                result_dao,
            )
