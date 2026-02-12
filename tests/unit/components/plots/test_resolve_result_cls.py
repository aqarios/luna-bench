import pytest

from luna_bench.components.plots.utils.resolve_result_cls import resolve_run_return_type
from luna_bench.types import MetricResult


class _NoAnnotation:
    __module__ = __name__

    def run(self) -> None:
        pass


class _GoodResult(MetricResult):
    value: float


class _HasAnnotation:
    __module__ = __name__

    def run(self) -> _GoodResult:
        return _GoodResult(value=1.0)


class TestResolveRunReturnType:
    def test_returns_annotated_type(self) -> None:
        result = resolve_run_return_type(_HasAnnotation, MetricResult)
        assert result is _GoodResult

    def test_raises_when_no_return_annotation(self) -> None:
        class _NoReturn:
            __module__ = __name__

            def run(self) -> None:
                pass

        # run() -> None means the annotation is there but it's None,
        # which is not a subclass of MetricResult.
        with pytest.raises(TypeError, match="return a MetricResult subclass"):
            resolve_run_return_type(_NoReturn, MetricResult)

    def test_raises_when_no_annotation_at_all(self) -> None:
        class _Missing:
            __module__ = __name__

        _Missing.run = None  # type: ignore[attr-defined]

        with pytest.raises(TypeError, match="no return type annotation"):
            resolve_run_return_type(_Missing, MetricResult)

    def test_raises_when_wrong_base(self) -> None:
        class _WrongResult:
            value: float

        class _BadMetric:
            __module__ = __name__

            def run(self) -> _WrongResult:
                return _WrongResult()

        with pytest.raises(TypeError, match="return a MetricResult subclass"):
            resolve_run_return_type(_BadMetric, MetricResult)
