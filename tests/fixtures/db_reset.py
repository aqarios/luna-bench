from collections.abc import Generator

import pytest

from luna_bench._internal.dao import DaoTransaction


@pytest.fixture(autouse=True)
def rest_db_each_time() -> Generator[DaoTransaction]:
    from luna_bench import _dao_container

    with _dao_container.transaction() as t:
        try:
            yield t
        finally:
            t.rollback()
