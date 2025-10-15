from collections.abc import Generator

import pytest

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench.configs.config import Config


@pytest.fixture()
def configured_dao() -> DaoTransaction:
    sc = DaoContainer()

    cnf = Config()
    cnf.DB_CONNECTION_STRING = ":memory:"

    sc.config.from_pydantic(cnf)
    sc.reset_singletons()
    sc.wire()
    return sc.transaction()


@pytest.fixture()
def empty_transaction(configured_dao: DaoTransaction) -> Generator[DaoTransaction]:
    """Provide a transaction fixture for testing DAOs."""
    with configured_dao as t:
        try:
            yield t
        finally:
            t.rollback()
