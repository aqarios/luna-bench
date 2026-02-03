from __future__ import annotations

from enum import Enum


class VarScope(str, Enum):
    """Scope of variables included in the calculation."""

    CONTINUOUS = "continuous"  # x ∈ R
    NON_CONTINUOUS = "non_continuous"  # x ∈ Z union {0, 1}
    ALL = "all"  # x ∈ R union Z union {0, 1}
