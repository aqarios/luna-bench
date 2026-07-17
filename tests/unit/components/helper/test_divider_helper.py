import pytest
from pydantic.fields import FieldInfo

from luna_bench.helpers.divider_helper import get_ratio, snap_to_bounds


class TestSnapToBounds:
    """Class tests the snap_to_bounds function."""

    @pytest.fixture()
    def bounded_field_info(self) -> FieldInfo:
        return FieldInfo(ge=0.0, le=1.0)

    def test_snaps_to_lower_bound(self, bounded_field_info: FieldInfo) -> None:
        snap = snap_to_bounds(value=-1e-9, field_info=bounded_field_info, abs_tol=1e-6)
        assert snap == 0.0

    def test_snaps_to_upper_bound(self, bounded_field_info: FieldInfo) -> None:
        snap = snap_to_bounds(value=1.0 + 1e-9, field_info=bounded_field_info, abs_tol=1e-6)
        assert snap == 1.0

    def test_value_within_bounds_is_unchanged(self, bounded_field_info: FieldInfo) -> None:
        snap = snap_to_bounds(value=0.5, field_info=bounded_field_info, abs_tol=1e-6)
        assert snap == 0.5

    def test_value_outside_tolerance_is_unchanged(self, bounded_field_info: FieldInfo) -> None:
        snap = snap_to_bounds(value=0.001, field_info=bounded_field_info, abs_tol=1e-6)
        assert snap == 0.001

    def test_field_without_bounds_is_unchanged(self) -> None:
        snap = snap_to_bounds(value=0.5, field_info=FieldInfo(), abs_tol=1e-6)
        assert snap == 0.5

    def test_field_with_only_lower_bound(self) -> None:
        field_info = FieldInfo(ge=0.0)
        snap = snap_to_bounds(value=1e-9, field_info=field_info, abs_tol=1e-6)
        assert snap == 0.0

    def test_field_with_only_upper_bound(self) -> None:
        field_info = FieldInfo(le=1.0)
        snap = snap_to_bounds(value=1.0 - 1e-9, field_info=field_info, abs_tol=1e-6)
        assert snap == 1.0


class TestGetRatio:
    """Class tests the get_ratio function."""

    def test_get_ratio(self) -> None:
        ratio = get_ratio(nominator=0.5, denominator=1.0, abt_diff=1e-6)
        assert ratio == 0.5

    def test_zero_division(self) -> None:
        with pytest.raises(ZeroDivisionError):
            get_ratio(nominator=0.5, denominator=0, abt_diff=1e-6)
