from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def bg_algorithm_runner() -> MagicMock:
    from luna_bench import _bg_task_container

    mock: MagicMock = _bg_task_container.bg_algorithm_runner()  # type: ignore[assignment] # Overwritten in testsetup
    assert isinstance(mock, MagicMock), (
        "The task container was not overwritten. This needs to be done in the test setup."
    )
    mock.reset_mock()
    return mock
