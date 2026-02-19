import pytest

from luna_bench.components.metrics.runtime import Runtime, RuntimeResult
from luna_bench.components.plots.utils.resolve_result_cls import resolve_run_return_type
from luna_bench.types import MetricResult


class TestResolveRunReturnType:
    def test_returns_annotated_type(self) -> None:
        result = resolve_run_return_type(Runtime, MetricResult)
        assert result is RuntimeResult

    def test_raises_when_no_return_annotation(self) -> None:
        class _NoReturn:
            __module__ = __name__

            def run(self) -> None:
                pass

        # run() -> None means the annotation is there but it's None,
        # which is not a subclass of MetricResult.
        with pytest.raises(TypeError, match="return a MetricResult subclass"):
            resolve_run_return_type(_NoReturn, MetricResult)  # type: ignore[arg-type]

    def test_raises_when_no_annotation_at_all(self) -> None:
        class _Missing:
            __module__ = __name__

        _Missing.run = None  # type: ignore[attr-defined]

        with pytest.raises(TypeError, match="no return type annotation"):
            resolve_run_return_type(_Missing, MetricResult)  # type: ignore[arg-type]

    def test_raises_when_wrong_base(self) -> None:
        class _WrongResult:
            value: float

        class _BadMetric:
            __module__ = __name__

            def run(self) -> _WrongResult:
                return _WrongResult()

        with pytest.raises(TypeError, match="return a MetricResult subclass"):
            resolve_run_return_type(_BadMetric, MetricResult)  # type: ignore[arg-type]
