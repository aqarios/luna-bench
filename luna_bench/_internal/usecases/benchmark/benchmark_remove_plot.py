from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkRemovePlotUc


class BenchmarkRemovePlotUcImpl(BenchmarkRemovePlotUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkRemovePlotUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, benchmark_name: str, plot_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.plot.remove_plot(benchmark_name, plot_name)
