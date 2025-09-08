from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.domain_models import ModelmetricConfigDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkAddModelMetricUc


class BenchmarkAddModelMetricUcImpl(BenchmarkAddModelMetricUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkAddModelMetricUc with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark_name: str, modelmetric_name: str, modelmetric_config: ModelmetricConfigDomain.ModelmetricConfig
    ) -> Result[ModelmetricConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.model_metric.add_modelmetric(benchmark_name, modelmetric_name, modelmetric_config)
