from dependency_injector.wiring import Provide, inject
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import BenchmarkDomain
from luna_bench._internal.mappers.container import MapperContainer
from luna_bench._internal.mappers.types import Mapper
from luna_bench._internal.user_models import (
    BenchmarkUserModel,
)
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkLoadAllUc


class BenchmarkLoadAllUcImpl(BenchmarkLoadAllUc):
    _transaction: DaoTransaction
    _benchmark_mapper: Mapper[BenchmarkDomain, BenchmarkUserModel]

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        benchmark_mapper: Mapper[BenchmarkDomain, BenchmarkUserModel] = Provide[MapperContainer.benchmark_mapper],
    ) -> None:
        """
        Initialize the BenchmarkLoadAllUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        benchmark_mapper: Mapper[BenchmarkDomain, BenchmarkUserModel]
            Benchmark mapper.
        """
        self._transaction = transaction
        self._benchmark_mapper = benchmark_mapper

    def __call__(self) -> Result[list[BenchmarkUserModel], UnknownLunaBenchError | UnknownIdError | ValidationError]:
        with self._transaction as t:
            result_dao: Result[list[BenchmarkDomain], UnknownLunaBenchError] = t.benchmark.load_all()

            to_return: list[BenchmarkUserModel] = []

            if not is_successful(result_dao):
                return Failure(result_dao.failure())
            benchmark_domains: list[BenchmarkDomain] = result_dao.unwrap()

            for benchmark_domain in benchmark_domains:
                user_model = self._benchmark_mapper.to_user_model(
                    benchmark_domain,
                )
                if not is_successful(user_model):
                    return Failure(user_model.failure())
                to_return.append(user_model.unwrap())
            return Success(to_return)
