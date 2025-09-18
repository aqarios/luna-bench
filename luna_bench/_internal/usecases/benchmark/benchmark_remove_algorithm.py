from returns.result import Result

from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.usecases.benchmark.protocols import BenchmarkRemoveAlgorithmUc
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BenchmarkRemoveAlgorithmUcImpl(BenchmarkRemoveAlgorithmUc):
    _transaction: DaoTransaction

    def __init__(self, transaction: DaoTransaction) -> None:
        """
        Initialize the BenchmarkRemoveAlgorithmUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.algorithm.remove(benchmark_name, solvejob_name)
