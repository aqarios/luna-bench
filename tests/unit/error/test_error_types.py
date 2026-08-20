import pytest

from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.incompatible_class_error import IncompatibleClassError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.model_name_already_used_error import ModelNameAlreadyUsedError


class TestModelNameAlreadyUsedError:
    def test_message_names_the_model(self) -> None:
        error = ModelNameAlreadyUsedError("my_model")

        assert "my_model" in str(error)

    def test_message_explains_that_names_are_database_wide(self) -> None:
        # The clash is not with this modelset but with the whole database, which
        # the bare "already exists" wording does not convey.
        message = str(ModelNameAlreadyUsedError("my_model"))

        assert "modelset" in message
        assert "unique" in message


class TestModelDecodingError:
    def test_retains_the_wrapped_exception(self) -> None:
        wrapped = ValueError("bad bytes")
        error = ModelDecodingError(b"\x00\x01", wrapped)

        assert error.error() is wrapped
        assert error.model_bytes == b"\x00\x01"

    def test_message_shows_the_offending_bytes(self) -> None:
        error = ModelDecodingError(b"\x00\x01", ValueError("bad bytes"))

        assert repr(b"\x00\x01") in str(error)


class TestIncompatibleClassError:
    def test_names_a_single_base_class(self) -> None:
        error = IncompatibleClassError(ValueError)

        assert error.base_class is ValueError
        assert "ValueError" in str(error)

    def test_names_every_base_class_in_a_tuple(self) -> None:
        error = IncompatibleClassError((ValueError, TypeError))

        assert "ValueError" in str(error)
        assert "TypeError" in str(error)

    @pytest.mark.parametrize(
        ("base", "expected"),
        [(object(), "object object at"), ((object(),), "object object at")],
        ids=["single_instance", "tuple_of_instances"],
    )
    def test_falls_back_to_repr_for_objects_without_a_name(self, base: object, expected: str) -> None:
        error = IncompatibleClassError(base)  # type: ignore[arg-type]

        assert expected in str(error)


class TestDataNotExistError:
    def test_falls_back_to_a_generic_message(self) -> None:
        assert str(DataNotExistError()) == "The requested data does not exist."

    def test_carries_a_caller_supplied_message(self) -> None:
        error = DataNotExistError("Benchmark 'b' has no modelset.")

        assert str(error) == "Benchmark 'b' has no modelset."
