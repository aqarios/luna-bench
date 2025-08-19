from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench.configs.config import Config

from .mock_model import _dummy_model

if TYPE_CHECKING:
    from luna_bench._internal.dao import StorageTransaction


@pytest.fixture()
def usecase() -> Generator[UsecaseContainer]:
    """Provide a usecase fixture for testing usecases."""
    uc = UsecaseContainer()

    cnf = Config()
    cnf.DB_CONNECTION_STRING = ":memory:"

    uc.config.from_pydantic(cnf)

    uc.reset_singletons()
    uc.wire()

    # Get the transaction from the container
    transaction: StorageTransaction = uc.storage_container.transaction()
    db = uc.storage_container.database()
    # Create tables

    with transaction as t:
        m1 = t.model.get_or_create(
            model_name="M1", model_hash=_dummy_model("M1").__hash__(), binary=_dummy_model("M1").encode()
        ).unwrap()
        m2 = t.model.get_or_create(
            model_name="M2", model_hash=_dummy_model("M2").__hash__(), binary=_dummy_model("M2").encode()
        ).unwrap()
        ms1 = t.modelset.create(modelset_name="MS1").unwrap()
        t.modelset.add_model(modelset_name=ms1.name, model_id=m1.id)
        t.modelset.add_model(modelset_name=ms1.name, model_id=m2.id)

    with db.atomic() as db_txn:
        try:
            yield uc
        finally:
            db_txn.rollback()
