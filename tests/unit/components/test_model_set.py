from __future__ import annotations

import logging
from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

import luna_bench
from luna_bench import ModelMetadata, ModelSet
from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.usecases.modelset.protocols import (
    ModelAddUc,
    ModelFetchUc,
    ModelLoadAllUc,
    ModelRemoveUc,
    ModelSetCreateUc,
    ModelSetDeleteUc,
    ModelSetLoadAllUc,
    ModelSetLoadUc,
)
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.utils.luna_model import simple_model, write_encoded_model_file, write_model_file

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from luna_model import Model


class TestModelData:
    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(ModelSetDomain(id=1, name="Test", models=[])),
                nullcontext(ModelSet(id=1, name="Test", models=[])),
            ),
            (
                Failure(UnknownLunaBenchError(RuntimeError("boom"))),
                pytest.raises(RuntimeError),
            ),
        ],
        ids=["success", "unexpected_failure"],
    )
    def test_create(
        self,
        return_value: Result[ModelSetDomain, Exception],
        exp: AbstractContextManager[ModelSet],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetCreateUc)
        mock.return_value = return_value
        with exp as e, luna_bench._usecase_container.modelset_create_uc.override(mock):
            r = ModelSet.create(modelset_name="Test")
            mock.assert_called_with(modelset_name="Test")

            assert e == r

    @pytest.mark.parametrize(
        ("modelset_name", "load_return_value", "exp"),
        [
            (
                "Test",
                Success(ModelSetDomain(id=1, name="Test", models=[])),
                nullcontext(ModelSet(id=1, name="Test", models=[])),
            ),
            (
                "Existing",
                Success(ModelSetDomain(id=2, name="Existing", models=[])),
                nullcontext(ModelSet(id=2, name="Existing", models=[])),
            ),
        ],
    )
    def test_create_when_duplicate(
        self,
        modelset_name: str,
        load_return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp: AbstractContextManager[ModelSet],
    ) -> None:
        create_mock: Mock = Mock(spec=ModelSetCreateUc)
        create_mock.return_value = Failure(DataNotUniqueError())

        load_mock: Mock = Mock(spec=ModelSetLoadUc)
        load_mock.return_value = load_return_value

        with (
            exp as e,
            luna_bench._usecase_container.modelset_create_uc.override(create_mock),
            luna_bench._usecase_container.modelset_load_uc.override(load_mock),
        ):
            r = ModelSet.create(modelset_name=modelset_name)
            create_mock.assert_called_with(modelset_name=modelset_name)
            assert e == r

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            ([ModelMetadataDomain(id=1, name="A", hash=1)], [ModelMetadata(id=1, name="A", hash=1)]),
            ([], []),
        ],
    )
    def test_load_all_models(self, return_value: list[ModelMetadataDomain], exp: list[ModelMetadata]) -> None:
        mock: Mock = Mock(spec=ModelLoadAllUc)
        mock.return_value = return_value
        with luna_bench._usecase_container.model_load_all_uc.override(mock):
            r = ModelSet.load_all_models()
            mock.assert_called_with()

        assert exp == r

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(ModelSetDomain(id=1, name="B", models=[ModelMetadataDomain(id=1, name="A", hash=1)])),
                nullcontext(ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])),
            ),
            (Failure(DataNotExistError()), pytest.raises(DataNotExistError)),
        ],
    )
    def test_add_model(
        self, return_value: Result[ModelSetDomain, Exception], exp: AbstractContextManager[ModelSet | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = return_value
        modelset = ModelSet(id=1, name="B", models=[])

        with exp as e, luna_bench._usecase_container.model_add_uc.override(mock):
            model = simple_model("A")
            modelset.add(model=model)
            mock.assert_called_with(modelset_name=return_value.unwrap().name, model=model)
            assert e == modelset

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success(ModelSetDomain(id=1, name="a", models=[])), nullcontext(ModelSet(id=1, name="a", models=[]))),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_load(
        self,
        return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp: AbstractContextManager[ModelSet | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetLoadUc)
        mock.return_value = return_value

        name: str = return_value.unwrap().name if is_successful(return_value) else "a"
        with exp as e, luna_bench._usecase_container.modelset_load_uc.override(mock):
            m = ModelSet.load(name=name)
            assert m == e

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success([]), nullcontext([])),
            (Success([ModelSetDomain(id=1, name="a", models=[])]), nullcontext([ModelSet(id=1, name="a", models=[])])),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_load_all(
        self,
        return_value: Result[list[ModelSetDomain], UnknownLunaBenchError],
        exp: AbstractContextManager[list[ModelSet] | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetLoadAllUc)
        mock.return_value = return_value

        with exp as e, luna_bench._usecase_container.modelset_load_all_uc.override(mock):
            assert ModelSet.load_all() == e
            mock.assert_called_once_with()

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success(ModelSetDomain(id=1, name="a", models=[])), nullcontext(ModelSet(id=1, name="a", models=[]))),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_remove_model(
        self,
        return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp: AbstractContextManager[ModelSet | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelRemoveUc)
        mock.return_value = return_value

        ms_name = "b"
        ms = ModelSet(id=1, name=ms_name, models=[ModelMetadata(id=1, name="A", hash=1)])
        with exp as e, luna_bench._usecase_container.model_remove_uc.override(mock):
            model = simple_model("A")
            ms.remove_model(model=model)

            assert ms == e
            mock.assert_called_once_with(modelset_name=ms_name, model=model)

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success(None), nullcontext(None)),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_delete(
        self, return_value: Result[None, UnknownLunaBenchError], exp: AbstractContextManager[ModelSet | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelSetDeleteUc)
        mock.return_value = return_value

        ms = ModelSet(id=1, name="b", models=[ModelMetadata(id=1, name="A", hash=1)])
        with exp, luna_bench._usecase_container.modelset_delete_uc.override(mock):
            ms.delete()

            mock.assert_called_once_with(modelset_name=ms.name)

    @pytest.mark.parametrize(
        ("models", "return_value", "exp_call_count", "exp"),
        [
            pytest.param(
                [simple_model("A"), simple_model("B")],
                Success(ModelSetDomain(id=1, name="B", models=[ModelMetadataDomain(id=2, name="B", hash=2)])),
                2,
                nullcontext(ModelSet(id=1, name="B", models=[ModelMetadata(id=2, name="B", hash=2)])),
                id="list_of_two_models",
            ),
            pytest.param(
                [],
                Success(ModelSetDomain(id=1, name="B", models=[])),
                0,
                nullcontext(ModelSet(id=1, name="B", models=[])),
                id="empty_list",
            ),
            pytest.param(
                [simple_model("A")],
                Failure(DataNotExistError()),
                1,
                pytest.raises(DataNotExistError),
                id="list_with_error",
            ),
        ],
    )
    def test_add_model_list(
        self,
        models: list[Model],
        return_value: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
        exp_call_count: int,
        exp: AbstractContextManager[ModelSet | DataNotExistError],
    ) -> None:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = return_value
        modelset = ModelSet(id=1, name="B", models=[])

        with exp as e, luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(model=models)

        assert mock.call_count == exp_call_count

        if is_successful(return_value):
            assert e == modelset

    @pytest.mark.parametrize(
        ("models", "return_value", "exp_call_count", "exp"),
        [
            pytest.param(
                iter([simple_model("A"), simple_model("B")]),
                Success(ModelSetDomain(id=1, name="B", models=[ModelMetadataDomain(id=2, name="B", hash=2)])),
                2,
                nullcontext(ModelSet(id=1, name="B", models=[ModelMetadata(id=2, name="B", hash=2)])),
                id="iterator_of_two_models",
            ),
            pytest.param(
                iter([]),
                Success(ModelSetDomain(id=1, name="B", models=[])),
                0,
                nullcontext(ModelSet(id=1, name="B", models=[])),
                id="empty_iterator",
            ),
            pytest.param(
                (m for m in [simple_model("A")]),
                Failure(DataNotExistError()),
                1,
                pytest.raises(DataNotExistError),
                id="generator_with_error",
            ),
        ],
    )
    def test_add_model_iterator(
        self,
        models: Iterable[Model],
        return_value: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
        exp_call_count: int,
        exp: AbstractContextManager[ModelSet | DataNotExistError],
    ) -> None:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = return_value
        modelset = ModelSet(id=1, name="B", models=[])

        with exp as e, luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(model=models)

        assert mock.call_count == exp_call_count

        if is_successful(return_value):
            assert e == modelset

    @pytest.mark.parametrize(
        ("models", "return_value", "exp_call_count", "exp"),
        [
            pytest.param(
                [simple_model("A"), simple_model("B")],
                Success(ModelSetDomain(id=1, name="B", models=[])),
                2,
                nullcontext(ModelSet(id=1, name="B", models=[])),
                id="list_of_two_models",
            ),
            pytest.param(
                [],
                Success(ModelSetDomain(id=1, name="B", models=[])),
                0,
                nullcontext(ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])),
                id="empty_list_is_a_no_op",
            ),
            pytest.param(
                iter([simple_model("A"), simple_model("B")]),
                Success(ModelSetDomain(id=1, name="B", models=[])),
                2,
                nullcontext(ModelSet(id=1, name="B", models=[])),
                id="iterator_of_two_models",
            ),
            pytest.param(
                (m for m in [simple_model("A")]),
                Failure(UnknownLunaBenchError(exception=RuntimeError())),
                1,
                pytest.raises(RuntimeError),
                id="generator_with_error",
            ),
        ],
    )
    def test_remove_model_iterable(
        self,
        models: Iterable[Model],
        return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp_call_count: int,
        exp: AbstractContextManager[ModelSet | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelRemoveUc)
        mock.return_value = return_value
        modelset = ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])

        with exp as e, luna_bench._usecase_container.model_remove_uc.override(mock):
            modelset.remove_model(model=models)

        assert mock.call_count == exp_call_count

        if is_successful(return_value):
            assert e == modelset


class TestAddFromPath:
    """``ModelSet.add`` accepting a file or a directory of model files."""

    @staticmethod
    def _add_mock(name: str = "B") -> Mock:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = Success(ModelSetDomain(id=1, name=name, models=[]))
        return mock

    def test_single_file_is_named_after_the_file_stem(self, tmp_path: Path) -> None:
        path = write_model_file(tmp_path, "alpha")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(path)

        assert mock.call_count == 1
        assert mock.call_args.kwargs["model"].name == "alpha"

    def test_directory_adds_every_model_file_sorted_by_name(self, tmp_path: Path) -> None:
        write_model_file(tmp_path, "gamma")
        write_model_file(tmp_path, "alpha")
        write_model_file(tmp_path, "beta", suffix=".lp")
        (tmp_path / "notes.txt").write_text("ignored")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(tmp_path)

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["alpha", "beta", "gamma"]

    def test_directory_given_as_str(self, tmp_path: Path) -> None:
        write_model_file(tmp_path, "alpha")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(str(tmp_path))

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["alpha"]

    def test_missing_path_raises_file_not_found(self, tmp_path: Path) -> None:
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(FileNotFoundError, match="m1"):
            modelset.add("m1")

        assert not (tmp_path / "m1").exists()

    def test_directory_without_model_files_raises_file_not_found(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text("no models here")
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(FileNotFoundError, match=r"\.mps"):
            modelset.add(tmp_path)

    def test_unsupported_suffix_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "alpha.txt"
        path.write_text("not a model")
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(ValueError, match=r"\.txt"):
            modelset.add(path)

    def test_iterable_may_mix_models_and_paths(self, tmp_path: Path) -> None:
        path = write_model_file(tmp_path, "alpha")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add([simple_model("handmade"), path])

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["handmade", "alpha"]

    def test_iterable_may_be_nested(self, tmp_path: Path) -> None:
        """Nesting is flattened to any depth, so a list of batches needs no unpacking."""
        path = write_model_file(tmp_path, "alpha")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add([[simple_model("handmade"), [path]], simple_model("outer")])

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["handmade", "alpha", "outer"]

    def test_remove_model_accepts_a_path(self, tmp_path: Path) -> None:
        path = write_model_file(tmp_path, "alpha")
        mock: Mock = Mock(spec=ModelRemoveUc)
        mock.return_value = Success(ModelSetDomain(id=1, name="B", models=[]))
        modelset = ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="alpha", hash=1)])

        with luna_bench._usecase_container.model_remove_uc.override(mock):
            modelset.remove_model(path)

        assert mock.call_count == 1
        assert mock.call_args.kwargs["model"].name == "alpha"


class TestAddFromEncodedFile:
    """A suffix ``Model.from_`` does not know is read as an encoded model."""

    @staticmethod
    def _add_mock(name: str = "B") -> Mock:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = Success(ModelSetDomain(id=1, name=name, models=[]))
        return mock

    def test_encoded_file_with_any_suffix_is_read(self, tmp_path: Path) -> None:
        path = write_encoded_model_file(tmp_path, "alpha", suffix=".whatever")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(path)

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["alpha"]

    def test_named_file_is_read_even_if_its_suffix_is_not_in_suffixes(self, tmp_path: Path) -> None:
        """Naming a file outright is instruction enough; ``suffixes`` only filters directories."""
        path = write_model_file(tmp_path, "alpha", suffix=".mps")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(path, suffixes=(".lp",))

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["alpha"]

    def test_file_that_is_neither_names_both_attempts(self, tmp_path: Path) -> None:
        path = tmp_path / "alpha.txt"
        path.write_text("not a model")
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(ValueError, match=r"alpha\.txt") as excinfo:
            modelset.add(path)

        message = str(excinfo.value)
        assert "not an encoded model" in message
        assert "Model.encode" in message

    def test_text_model_under_a_wrong_suffix_is_not_sniffed(self, tmp_path: Path) -> None:
        """Passing file contents to ``Model.from_`` parses any text into an empty model.

        Sniffing would therefore turn a README into a model, so a mis-suffixed
        text model must raise rather than be guessed at.
        """
        source = write_model_file(tmp_path, "real", suffix=".mps")
        path = tmp_path / "alpha.model"
        path.write_bytes(source.read_bytes())
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(ValueError, match=r"alpha\.model"):
            modelset.add(path)


class TestAddDirectorySuffixes:
    """``suffixes`` decides what a directory scan picks up."""

    @staticmethod
    def _add_mock(name: str = "B") -> Mock:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = Success(ModelSetDomain(id=1, name=name, models=[]))
        return mock

    def test_custom_suffix_is_picked_up(self, tmp_path: Path) -> None:
        write_encoded_model_file(tmp_path, "alpha", suffix=".model")
        write_model_file(tmp_path, "beta", suffix=".mps")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(tmp_path, suffixes=(".model",))

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["alpha"]

    @pytest.mark.parametrize("given", [(".mps",), ("mps",)])
    def test_leading_dot_is_optional(self, tmp_path: Path, given: tuple[str, ...]) -> None:
        write_model_file(tmp_path, "alpha", suffix=".mps")
        mock = self._add_mock()
        modelset = ModelSet(id=1, name="B", models=[])

        with luna_bench._usecase_container.model_add_uc.override(mock):
            modelset.add(tmp_path, suffixes=given)

        assert [call.kwargs["model"].name for call in mock.call_args_list] == ["alpha"]

    def test_matching_is_case_sensitive_like_from_(self, tmp_path: Path) -> None:
        """``Model.from_`` rejects ``.MPS``, so discovery must not offer it up."""
        write_model_file(tmp_path, "alpha", suffix=".MPS")
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(FileNotFoundError, match="contains no"):
            modelset.add(tmp_path)

    def test_empty_suffixes_raises_value_error(self, tmp_path: Path) -> None:
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(ValueError, match="suffixes is empty"):
            modelset.add(tmp_path, suffixes=())

    def test_directory_error_points_at_suffixes(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text("no models here")
        modelset = ModelSet(id=1, name="B", models=[])

        with pytest.raises(FileNotFoundError, match="suffixes"):
            modelset.add(tmp_path)


class TestAddIsRerunnable:
    """Re-running the same script must not duplicate models nor raise."""

    @staticmethod
    def _fetch_mock(model: Model) -> Mock:
        """Mock the fetch of the model already stored under id 1."""
        mock: Mock = Mock(spec=ModelFetchUc)
        mock.return_value = Success(model)
        return mock

    def test_model_already_in_the_set_is_skipped_with_a_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        stored = simple_model("A")
        modelset = ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])
        add_mock: Mock = Mock(spec=ModelAddUc)

        with (
            caplog.at_level(logging.WARNING),
            luna_bench._usecase_container.model_add_uc.override(add_mock),
            luna_bench._usecase_container.model_fetch_uc.override(self._fetch_mock(stored)),
        ):
            modelset.add(simple_model("A"))

        add_mock.assert_not_called()
        assert [m.name for m in modelset.models] == ["A"]
        assert "already" in caplog.text

    def test_same_name_but_different_content_is_still_delegated(self) -> None:
        stored = simple_model("A")
        modelset = ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])
        changed = simple_model("A")
        changed.constraints += changed.get_variable("x") <= 3
        add_mock: Mock = Mock(spec=ModelAddUc)
        add_mock.return_value = Success(ModelSetDomain(id=1, name="B", models=[]))

        with (
            luna_bench._usecase_container.model_add_uc.override(add_mock),
            luna_bench._usecase_container.model_fetch_uc.override(self._fetch_mock(stored)),
        ):
            modelset.add(changed)

        add_mock.assert_called_once_with(modelset_name="B", model=changed)

    def test_model_whose_contents_cannot_be_read_is_left_to_the_use_case(self) -> None:
        modelset = ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])
        fetch_mock: Mock = Mock(spec=ModelFetchUc)
        fetch_mock.return_value = Failure(DataNotExistError())
        add_mock: Mock = Mock(spec=ModelAddUc)
        add_mock.return_value = Success(ModelSetDomain(id=1, name="B", models=[]))
        model = simple_model("A")

        with (
            luna_bench._usecase_container.model_add_uc.override(add_mock),
            luna_bench._usecase_container.model_fetch_uc.override(fetch_mock),
        ):
            modelset.add(model)

        add_mock.assert_called_once_with(modelset_name="B", model=model)


class TestIterableRemovalIsNotAtomic:
    """Removal applies model by model, so a failure must say what already went."""

    def test_failure_names_what_was_already_removed(self) -> None:
        first = simple_model("first")
        second = simple_model("second")
        modelset = ModelSet(
            id=1,
            name="set_x",
            models=[ModelMetadata(id=1, name="first", hash=1), ModelMetadata(id=2, name="second", hash=2)],
        )
        mock: Mock = Mock(spec=ModelRemoveUc)
        mock.side_effect = [
            Success(ModelSetDomain(id=1, name="set_x", models=[ModelMetadataDomain(id=2, name="second", hash=2)])),
            Failure(DataNotExistError()),
        ]

        with pytest.raises(RuntimeError) as exc_info, luna_bench._usecase_container.model_remove_uc.override(mock):
            modelset.remove_model([first, second])

        message = str(exc_info.value)
        assert "first" in message, "the model that was already removed must be named"
        assert "second" in message, "the model the batch failed on must be named"
        assert "set_x" in message

    def test_a_single_model_failure_is_not_dressed_up(self) -> None:
        modelset = ModelSet(id=1, name="set_x", models=[])
        mock: Mock = Mock(spec=ModelRemoveUc)
        mock.return_value = Failure(DataNotExistError())

        with pytest.raises(RuntimeError) as exc_info, luna_bench._usecase_container.model_remove_uc.override(mock):
            modelset.remove_model(simple_model("first"))

        assert "already removed" not in str(exc_info.value)
