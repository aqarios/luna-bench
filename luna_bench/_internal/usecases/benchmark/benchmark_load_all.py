from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from ...domain_models import BenchmarkDomain
from .protocols import BenchmarkLoadAllUc


class BenchmarkLoadAllUcImpl(BenchmarkLoadAllUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkLoadAllUc with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self) -> Result[list[BenchmarkDomain], UnknownLunaBenchError]:
        with self._transaction as t:
            return t.benchmark.load_all()
