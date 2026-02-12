"""Resolve the return type annotation of a component's ``run`` method."""

from __future__ import annotations

import sys
from typing import Any


def resolve_run_return_type(cls: type, expected_base: type) -> type:
    """Extract and validate the return type of ``cls.run()``.

    Parameters
    ----------
    cls:
        A component class (metric, feature, …) whose ``run`` method has a
        return-type annotation.
    expected_base:
        The base class the resolved return type must be a subclass of.

    Returns
    -------
    type
        The concrete return type.

    Raises
    ------
    TypeError
        If the annotation is missing or doesn't satisfy *expected_base*.
    """
    run_method = getattr(cls, "run", None)
    annotations = getattr(run_method, "__annotations__", {})
    if "return" not in annotations:
        msg = f"{cls.__name__}.run() has no return type annotation"
        raise TypeError(msg)
    raw: Any = annotations["return"]
    if isinstance(raw, str):
        module = sys.modules.get(cls.__module__, None)
        globalns = vars(module) if module else {}
        raw = eval(raw, globalns)  # noqa: S307
    if not (isinstance(raw, type) and issubclass(raw, expected_base)):
        msg = f"Expected {cls.__name__}.run() to return a {expected_base.__name__} subclass, got {raw}"
        raise TypeError(msg)
    return raw
