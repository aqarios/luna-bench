from __future__ import annotations

from luna_bench.errors.unknown_error import UnknownLunaBenchError


class TestErrorWrapper:
    def test_error_wrapper(self) -> None:
        test_error = RuntimeError("test error")
        wrapped_error = UnknownLunaBenchError(test_error)

        assert wrapped_error.error() == test_error
