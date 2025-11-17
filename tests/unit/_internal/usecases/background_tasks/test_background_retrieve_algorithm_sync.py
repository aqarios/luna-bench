from unittest.mock import MagicMock, patch

import pytest
from luna_quantum import Solution
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.background_tasks.background_retrieve_algorithm_sync import (
    BackgroundRetrieveAlgorithmSyncUcImpl,
)
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRetrieveAlgorithmSyncUc
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

PATCH_TARGET = (
    "luna_bench._internal.usecases.background_tasks.background_retrieve_algorithm_sync."
    "HueyAlgorithmRunner.retrieve_task_result"
)
solution = MagicMock(spec=Solution)


class TestBackgroundRetrieveAlgorithmSync:
    @patch(PATCH_TARGET)
    @pytest.mark.parametrize(
        ("uc", "mocked_return", "exp"),
        [
            (BackgroundRetrieveAlgorithmSyncUcImpl(), Success(solution), Some(Success(solution))),
            (BackgroundRetrieveAlgorithmSyncUcImpl(), None, Nothing),
            (
                BackgroundRetrieveAlgorithmSyncUcImpl(),
                "",
                Some(Failure(UnknownLunaBenchError(ValueError(f"Unexpected result type: {str}")))),
            ),
            (
                BackgroundRetrieveAlgorithmSyncUcImpl(),
                Failure(ModelDecodingError(b"", ValueError(""))),
                Some(Failure(ModelDecodingError(b"", ValueError("")))),
            ),
        ],
    )
    def test_returns_correct_value(
        self,
        mock_retrieve_task_result: MagicMock,
        uc: BackgroundRetrieveAlgorithmSyncUc,
        mocked_return: Result[Solution, Exception],
        exp: Maybe[Result[Solution, Exception]],
    ) -> None:
        mock_retrieve_task_result.return_value = mocked_return

        result = uc(task_id="some_id")

        mock_retrieve_task_result.assert_called_once_with("some_id")

        assert type(result) is type(exp)
        if is_successful(exp):
            unwrapped_result = result.unwrap()
            unwrapped_exp = exp.unwrap()

            assert type(unwrapped_result) is type(unwrapped_exp)
            assert unwrapped_result.__str__() == unwrapped_exp.__str__()
