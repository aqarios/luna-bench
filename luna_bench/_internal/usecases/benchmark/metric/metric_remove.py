from dependency_injector.wiring import Provide, inject
from returns.result import Result

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.usecases.benchmark.protocols import MetricRemoveUc
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class MetricRemoveUcImpl(MetricRemoveUc):
    _transaction: DaoTransaction

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
    ) -> None:
        """
        Initialize the BenchmarkRemoveMetricUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.metric.remove(benchmark_name, metric_name)
