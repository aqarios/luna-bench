from typing import Any

import pytest
from luna_quantum import Model, Solution
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.background_tasks import HueyAlgorithmRunner
from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import AlgorithmAsync, AlgorithmSync
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_model import _dummy_model

_model: Model = _dummy_model("a")
_solution: Solution = Solution._build(  # type: ignore[attr-defined]
    component_types=[],
    binary_cols=[],
    spin_cols=None,
    int_cols=None,
    real_cols=None,
    raw_energies=None,
    timing=None,
    counts=[],
)


class SuccessAlgorithmSync(AlgorithmSync):
    def run(self, model: Model) -> Solution:  # noqa: ARG002
        return _solution


class SuccessAlgorithmAsync(AlgorithmAsync[ArbitraryDataDomain]):
    @property
    def model_type(self) -> type[ArbitraryDataDomain]:
        return ArbitraryDataDomain

    def run_async(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        return ArbitraryDataDomain()

    def fetch_result(self, model: Model, retrieval_data: ArbitraryDataDomain) -> Solution:  # noqa: ARG002
        return _solution


class FailureAlgorithmSync(AlgorithmSync):
    def run(self, model: Model) -> Solution:  # noqa: ARG002
        raise RuntimeError


class FailureAlgorithmAsync(AlgorithmAsync[ArbitraryDataDomain]):
    @property
    def model_type(self) -> type[ArbitraryDataDomain]:
        return ArbitraryDataDomain

    def run_async(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        raise RuntimeError

    def fetch_result(self, model: Model, retrieval_data: ArbitraryDataDomain) -> Solution:  # noqa: ARG002
        raise RuntimeError


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
            assert unwrapped_result.__str__() == unwrapped_exp.__str__()

        else:
            assert result.failure().__class__ is exp.failure().__class__

    @pytest.mark.parametrize(
        ("model_id", "algorithm", "exp"),
        [
            (1, SuccessAlgorithmSync(), Success(_solution)),
            (2, SuccessAlgorithmSync(), Failure(ModelDecodingError(b"", AssertionError()))),
            (1, FailureAlgorithmSync(), Failure(RunAlgorithmRuntimeError(RuntimeError()))),
        ],
    )
    def test_run_sync(
        self,
        transaction: DaoTransaction,  # noqa: ARG002
        model_id: int,
        algorithm: AlgorithmSync,
        exp: Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = HueyAlgorithmRunner._run_sync(algorithm, model_id)

        assert type(result) is type(exp)
        if is_successful(result):
            unwrapped_result = result.unwrap()
            unwrapped_exp = exp.unwrap()
            assert unwrapped_result.__str__() == unwrapped_exp.__str__()

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
        algorithm: AlgorithmAsync[Any],
        exp: Result[BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = HueyAlgorithmRunner._run_async(algorithm, model_id)

        assert type(result) is type(exp)
        if is_successful(result):
            unwrapped_result = result.unwrap()
            unwrapped_exp = exp.unwrap()
            assert unwrapped_result.__str__() == unwrapped_exp.__str__()

        else:
            assert result.failure().__class__ is exp.failure().__class__
