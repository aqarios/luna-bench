from unittest.mock import MagicMock

from luna_bench._internal.usecases.background_tasks.background_run_algorithm_async import (
    BackgroundRunAlgorithmAsyncUcImpl,
)
from luna_bench.custom import BaseAlgorithmAsync


class TestBackgroundRunAlgorithmAsync:
    def test_call_delegates_to_runner(self) -> None:
        bg_runner = MagicMock()
        bg_runner.run_async.return_value = "task_99"

        uc = BackgroundRunAlgorithmAsyncUcImpl(bg_algorithm_runner=bg_runner)
        result = uc(MagicMock(spec=BaseAlgorithmAsync), model_id=2)

        assert result == "task_99"
        bg_runner.run_async.assert_called_once()
