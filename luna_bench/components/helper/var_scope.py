from __future__ import annotations

from enum import Enum


class VarScope(str, Enum):
    """Scope of variables included in the calculation."""

    CONTINUOUS = "continuous"  # Real/continuous variables only
    NON_CONTINUOUS = "non_continuous"  # Integer + Binary variables
    ALL = "all"  # All variable types
