from collections.abc import Generator

import pytest

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench.configs.config import Config


@pytest.fixture()
def empty_transaction() -> Generator[DaoTransaction]:
    """Provide a transaction fixture for testing DAOs."""
    sc = DaoContainer()

    cnf = Config()
    cnf.DB_CONNECTION_STRING = ":memory:"

    sc.config.from_pydantic(cnf)
    sc.reset_singletons()
    sc.wire()

    transaction: DaoTransaction = sc.transaction()

    with transaction as t:
        try:
            yield t
        finally:
            t.rollback()
