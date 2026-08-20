import pytest

from luna_bench.errors.base_error import BaseError
from luna_bench.errors.modelset_not_loaded_error import ModelSetNotLoadedError


class TestModelSetNotLoadedError:
    def test_is_base_error(self) -> None:
        assert issubclass(ModelSetNotLoadedError, BaseError)

    def test_stores_names(self) -> None:
        error = ModelSetNotLoadedError("my_bench", "my_models")

        assert error.benchmark_name == "my_bench"
        assert error.modelset_name == "my_models"

    def test_message_names_the_missing_modelset_and_the_fix(self) -> None:
        error = ModelSetNotLoadedError("my_bench", "my_models")

        message = str(error)
        assert "my_bench" in message
        assert "could not be loaded" in message
        assert 'ModelSet.create("my_models")' in message

    def test_is_raisable(self) -> None:
        with pytest.raises(ModelSetNotLoadedError):
            raise ModelSetNotLoadedError("my_bench", "my_models")
