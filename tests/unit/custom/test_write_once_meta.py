import pytest

from luna_bench.custom.base_components.meta_classes.write_once_meta import WriteOnceMeta
from luna_bench.errors.write_once_error import WriteOnceError


class _TestMeta(metaclass=WriteOnceMeta):
    write_once_fields: dict[str, type] = {"locked": str}  # noqa: RUF012
    locked: str = "original"


class TestWriteOnceMeta:
    def test_setattr_raises_on_write_once_field(self) -> None:
        with pytest.raises(WriteOnceError, match="field 'locked' for the class '_TestMeta'"):
            _TestMeta.locked = "overwrite"
