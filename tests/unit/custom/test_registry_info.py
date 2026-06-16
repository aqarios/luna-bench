from __future__ import annotations

import pytest

from luna_bench.custom import RegistryInfo

_NON_EMPTY = "NON_EMPTY"


class TestRegistryInfo:
    @pytest.mark.parametrize(
        ("method_name", "expected"),
        [
            pytest.param("log_registry_contents", None, id="registry_contents"),
            pytest.param("log_registered_features", ["mock_feature"], id="features"),
            pytest.param("log_registered_sync", _NON_EMPTY, id="algorithms_sync"),
            pytest.param("log_registered_algorithms_async", _NON_EMPTY, id="algorithms_async"),
            pytest.param("log_registered_metrics", ["mock_metric"], id="metrics"),
            pytest.param("log_registered_plots", _NON_EMPTY, id="plots"),
        ],
    )
    def test_log_registered(self, method_name: str, expected: object) -> None:
        result = getattr(RegistryInfo, method_name)()

        if expected is None:
            assert result is None
        elif expected is _NON_EMPTY:
            assert isinstance(result, list)
            assert len(result) > 0
        else:
            assert isinstance(expected, list)
            assert isinstance(result, list)
            for rid in expected:
                assert rid in result, f"Expected {rid!r} in {result}"
