from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.domain_models.metric_config_domain import MetricConfigDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkAddMetricUc


class BenchmarkAddMetricUcImpl(BenchmarkAddMetricUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkMetricImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark_name: str, metric_name: str, metric_config: MetricConfigDomain.MetricConfig
    ) -> Result[MetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.metric.add_metric(benchmark_name, metric_name, metric_config)
