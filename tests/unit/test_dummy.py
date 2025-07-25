import pytest

from luna_bench._internal.entities import ModelSetDomain, StorageTransaction


@pytest.mark.parametrize("modelset_name", ["xD", "yD", "zD"])
def test_model_all_returns_list_of_models(empty_transaction: StorageTransaction, modelset_name: str):
    empty_transaction.modelset.create(modelset_name)

    all: list[ModelSetDomain] = empty_transaction.modelset.load_all().unwrap()
    assert len(all) == 1
    assert all[0].name == modelset_name
    # Further assertions here if needed


@pytest.mark.parametrize("modelset_name", ["xD", "yD", "zD"])
def test_model_all_returns_list_of_models2(empty_transaction: StorageTransaction, modelset_name: str):
    empty_transaction.modelset.create(modelset_name)

    all: list[ModelSetDomain] = empty_transaction.modelset.load_all().unwrap()
    assert len(all) == 1
    assert all[0].name == modelset_name
    # Further assertions here if needed
