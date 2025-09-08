from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkLoadUc


class BenchmarkLoadUcImpl(BenchmarkLoadUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkLoadUc with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, benchmark_name: str) -> Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.benchmark.load(benchmark_name)
