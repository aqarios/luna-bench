from typing import Any

import pytest
from luna_model import Model, Solution
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.background_tasks import SyncRunPayload
from luna_bench._internal.background_tasks.huey.huey_algorithm_runner import HueyAlgorithmRunner
from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.custom import BaseAlgorithmAsync, BaseAlgorithmSync, SolveOutcome
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.helpers.metadata import decode_metadata, encode_metadata
from tests.utils.luna_model import simple_model

_model: Model = simple_model("a")
_solution: Solution = Solution([])


class SuccessAlgorithmSync(BaseAlgorithmSync):
    def run(self, model: Model) -> Solution:  # noqa: ARG002
        return _solution


class MetadataAlgorithmSync(BaseAlgorithmSync):
    """Reports what it knows about the run alongside the solution."""

    def run(self, model: Model) -> SolveOutcome:  # noqa: ARG002
        return _solution, {"device": "qpu-7"}


class UnserializableMetadataAlgorithmSync(BaseAlgorithmSync):
    """Reports metadata holding something no serializer can carry across a process."""

    def run(self, model: Model) -> SolveOutcome:  # noqa: ARG002
        return _solution, {"connection": (i for i in range(3))}


class WrongShapeAlgorithmSync(BaseAlgorithmSync):
    """Returns neither a solution nor a (solution, metadata) pair."""

    def run(self, model: Model) -> SolveOutcome:  # noqa: ARG002
        return (_solution, {"a": 1}, "too much")  # type: ignore[return-value] # the point of the test


class SuccessAlgorithmAsync(BaseAlgorithmAsync[ArbitraryDataDomain]):
    @property
    def model_type(self) -> type[ArbitraryDataDomain]:
        return ArbitraryDataDomain

    def run_async(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        return ArbitraryDataDomain()

    def fetch_result(self, model: Model, retrieval_data: ArbitraryDataDomain) -> Result[Solution, str]:  # noqa: ARG002
        return Success(_solution)


class FailureAlgorithmSync(BaseAlgorithmSync):
    def run(self, model: Model) -> Solution:  # noqa: ARG002
        raise RuntimeError


class FailureAlgorithmAsync(BaseAlgorithmAsync[ArbitraryDataDomain]):
    @property
    def model_type(self) -> type[ArbitraryDataDomain]:
        return ArbitraryDataDomain

    def run_async(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        raise RuntimeError

    def fetch_result(self, model: Model, retrieval_data: ArbitraryDataDomain) -> Result[Solution, str]:  # noqa: ARG002
        raise Failure(RuntimeError)  # type: ignore[misc] # Fine here it's a fake failing algorithm


class TestHueyAlgorithmRunner:
    @pytest.fixture()
    def transaction(self, empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture for testing DAOs."""
        empty_transaction.model.get_or_create(
            model_name="a",
            model_hash=_model.__hash__(),
            binary=_model.encode(),
        )
        empty_transaction.model.get_or_create(model_name="b", model_hash=-1, binary=b"")
        return empty_transaction

    @pytest.mark.parametrize(
        ("model_id", "exp"),
        [
            (1, Success(_model)),
            (2, Failure(ModelDecodingError(b"", AssertionError()))),
            (3, Failure(DataNotExistError())),
        ],
    )
    def test_load_model(
        self,
        transaction: DaoTransaction,  # noqa: ARG002
        model_id: int,
        exp: Result[Model, ModelDecodingError | DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = HueyAlgorithmRunner._load_model(model_id)

        assert type(result) is type(exp)
        if is_successful(result):
            unwrapped_result = result.unwrap()
            unwrapped_exp = exp.unwrap()
            assert unwrapped_result.equal_contents(unwrapped_exp)

        else:
            assert result.failure().__class__ is exp.failure().__class__

    @pytest.mark.parametrize(
        ("model_id", "algorithm", "exp"),
        [
            (1, SuccessAlgorithmSync(), Success((_solution, None))),
            (1, MetadataAlgorithmSync(), Success((_solution, encode_metadata({"device": "qpu-7"})))),
            (2, SuccessAlgorithmSync(), Failure(ModelDecodingError(b"", AssertionError()))),
            (1, FailureAlgorithmSync(), Failure(RunAlgorithmRuntimeError(RuntimeError()))),
            # Metadata that cannot cross the process boundary, and a return value of the wrong
            # shape, are failed runs like any other - not a queue result nobody can decode.
            (1, UnserializableMetadataAlgorithmSync(), Failure(RunAlgorithmRuntimeError(RuntimeError()))),
            (1, WrongShapeAlgorithmSync(), Failure(RunAlgorithmRuntimeError(RuntimeError()))),
        ],
    )
    def test_run_sync(
        self,
        transaction: DaoTransaction,  # noqa: ARG002
        model_id: int,
        algorithm: BaseAlgorithmSync,
        exp: Result[SyncRunPayload, ModelDecodingError | DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = HueyAlgorithmRunner._run_sync(algorithm, model_id, "my_algorithm")

        assert type(result) is type(exp)
        if is_successful(result):
            solution, metadata = result.unwrap()
            expected_solution, expected_metadata = exp.unwrap()
            assert solution.__str__() == expected_solution.__str__()
            assert decode_metadata(metadata) == decode_metadata(expected_metadata)

        else:
            assert result.failure().__class__ is exp.failure().__class__

    @pytest.mark.parametrize(
        ("model_id", "algorithm", "exp"),
        [
            (1, SuccessAlgorithmAsync(), Success(ArbitraryDataDomain())),
            (2, SuccessAlgorithmAsync(), Failure(ModelDecodingError(b"", AssertionError()))),
            (1, FailureAlgorithmAsync(), Failure(RunAlgorithmRuntimeError(RuntimeError()))),
        ],
    )
    def test_run_async(
        self,
        transaction: DaoTransaction,  # noqa: ARG002
        model_id: int,
        algorithm: BaseAlgorithmAsync[Any],
        exp: Result[BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = HueyAlgorithmRunner._run_async(algorithm, model_id, "my_algorithm")
        assert type(result) is type(exp)
        if is_successful(result):
            unwrapped_result = result.unwrap()
            unwrapped_exp = exp.unwrap()
            assert unwrapped_result.__str__() == unwrapped_exp.__str__()

        else:
            assert result.failure().__class__ is exp.failure().__class__
