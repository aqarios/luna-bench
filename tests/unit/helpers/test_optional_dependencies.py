from __future__ import annotations

import pytest

from luna_bench.errors.missing_optional_dependency_error import (
    MissingOptionalDependencyError,
)
from luna_bench.helpers.optional_dependencies import check_optional_dependency


class TestCheckOptionalDependency:
    def test_import_exists(self) -> None:
        """`os` is always available — should not raise."""
        check_optional_dependency("os")

    def test_import_missing_raises(self) -> None:
        """A non-existent package should raise MissingOptionalDependencyError."""
        with pytest.raises(MissingOptionalDependencyError, match="nonexistent_pkg_xyz"):
            check_optional_dependency("nonexistent_pkg_xyz")
