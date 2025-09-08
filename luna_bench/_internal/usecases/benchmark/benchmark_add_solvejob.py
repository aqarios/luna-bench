from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.domain_models.solve_job_config_domain import SolveJobConfigDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import BenchmarkAddSolveJobUc


class BenchmarkAddSolveJobUcImpl(BenchmarkAddSolveJobUc):
    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the BenchmarkAddSolveJobUc with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(
        self, benchmark_name: str, solve_job_name: str, solve_job_config: SolveJobConfigDomain.SolveJobConfig
    ) -> Result[SolveJobConfigDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        with self._transaction as t:
            return t.solve_job.add_solvejob(benchmark_name, solve_job_name, solve_job_config)
