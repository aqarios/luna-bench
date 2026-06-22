from unittest.mock import MagicMock

from luna_bench._internal.usecases.background_tasks.background_run_algorithm_sync import (
    BackgroundRunAlgorithmSyncUcImpl,
)
from luna_bench.custom import BaseAlgorithmSync


class TestBackgroundRunAlgorithmSync:
    def test_call_delegates_to_runner(self) -> None:
        bg_runner = MagicMock()
        bg_runner.run_sync.return_value = "task_42"

        uc = BackgroundRunAlgorithmSyncUcImpl(bg_algorithm_runner=bg_runner)
        result = uc(MagicMock(spec=BaseAlgorithmSync), model_id=1)

        assert result == "task_42"
        bg_runner.run_sync.assert_called_once()
