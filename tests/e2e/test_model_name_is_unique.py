import pytest
from luna_model import Model

from luna_bench import ModelSet
from luna_bench._internal.dao import DaoTransaction
from tests.utils.luna_model import simple_model


class TestModelNameNotUnique:
    def test_model_name_not_unique(self, rest_db_each_time: DaoTransaction) -> None:
        model_set1 = ModelSet.create("model_set1")
        model_set2 = ModelSet.create("model_set2")

        model_set1.add(simple_model("name"))

        # Adding the same model multiple times must be possible
        model_set1.add(simple_model("name"))

        with pytest.raises(RuntimeError):
            model_set1.add(Model("name"))

        assert len(rest_db_each_time.model.get_all()) == 1

        with pytest.raises(RuntimeError):
            model_set2.add(Model("name"))
        assert len(rest_db_each_time.model.get_all()) == 1

        assert len(model_set1.models) == 1
        assert len(model_set2.models) == 0
