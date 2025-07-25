from collections.abc import Generator

import pytest

from luna_bench import _container
from luna_bench._internal.entities import StorageTransaction
from luna_bench._internal.entities.storage_container import StorageContainer
from luna_bench.configs.config import Config


@pytest.fixture()
def empty_transaction() -> Generator[StorageTransaction]:
    """Provide a transaction fixture for testing DAOs."""
    sc = StorageContainer()

    cnf = Config()
    cnf.DB_CONNECTION_STRING = ":memory:"

    sc.config.from_pydantic(cnf)
    sc.reset_singletons()
    sc.wire()

    # Get the transaction from the container
    transaction = _container.storage_container.transaction()
    db = _container.storage_container.database()
    # Create tables

    with db.atomic() as db_txn:
        try:
            yield transaction
        finally:
            db_txn.rollback()
