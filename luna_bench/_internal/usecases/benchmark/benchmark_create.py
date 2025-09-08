from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkCreateUc


class BenchmarkCreateUcImpl(BenchmarkCreateUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkCreateImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, benchmark_name: str) -> Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.benchmark.create(benchmark_name)
