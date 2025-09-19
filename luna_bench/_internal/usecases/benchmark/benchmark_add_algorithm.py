from returns.result import Result

from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.domain_models.algorithm_config_domain import AlgorithmConfigDomain
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkAddAlgorithmUc


class BenchmarkAddAlgorithmUcImpl(BenchmarkAddAlgorithmUc):
    _transaction: DaoTransaction

    def __init__(self, transaction: DaoTransaction) -> None:
        """
        Initialize the BenchmarkAddAlgorithmUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def __call__(
        self,
        benchmark_name: str,
        solve_job_name: str,
        algorithm: AlgorithmConfigDomain.Algorithm,
        backend: AlgorithmConfigDomain.Backend | None = None,
    ) -> Result[AlgorithmConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.algorithm.add(benchmark_name, solve_job_name, algorithm, backend)
