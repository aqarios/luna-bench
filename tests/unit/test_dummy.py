import pytest

from luna_bench._internal.entities import ModelSetDomain, StorageTransaction


@pytest.mark.parametrize("modelset_name", ["xD", "yD", "zD"])
def test_model_all_returns_list_of_models(empty_transaction: StorageTransaction, modelset_name: str) -> None:
    empty_transaction.modelset.create(modelset_name)

    model_sets: list[ModelSetDomain] = empty_transaction.modelset.load_all().unwrap()
    assert len(model_sets) == 1
    assert model_sets[0].name == modelset_name
    # Further assertions here if needed


@pytest.mark.parametrize("modelset_name", ["xD", "yD", "zD"])
def test_model_all_returns_list_of_models2(empty_transaction: StorageTransaction, modelset_name: str) -> None:
    empty_transaction.modelset.create(modelset_name)

    model_sets: list[ModelSetDomain] = empty_transaction.modelset.load_all().unwrap()
    assert len(model_sets) == 1
    assert model_sets[0].name == modelset_name
    # Further assertions here if needed
