from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.usecases.benchmark.protocols import BenchmarkRemoveSolveJobUc
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BenchmarkRemoveSolveJobUcImpl(BenchmarkRemoveSolveJobUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkRemoveSolveJobUc with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.solve_job.remove_solvejob(benchmark_name, solvejob_name)
