from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def rest_db_each_time() -> Generator[None]:
    from luna_bench import _dao_container

    with _dao_container.transaction() as t:
        try:
            yield
        finally:
            t.rollback()
