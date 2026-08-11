"""The generated ``__init__`` of every component must match its pydantic fields.

The signatures exist so IDEs can show the constructor options; a field that is added,
retyped, renamed, or given a new default without regenerating them would leave users
with a signature that lies. This test regenerates in memory and compares.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

    from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "type_hints.py"


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("type_hints", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


generator = _load_generator()


@pytest.mark.parametrize("component", generator.component_classes(), ids=lambda cls: cls.__name__)
def test_generated_init_matches_fields(component: type[BaseModel]) -> None:
    path, expected = generator.updated_source(component)

    assert path.read_text() == expected, (
        f"{component.__name__} has an outdated __init__ signature. "
        f"Run 'uv run python scripts/type_hints.py' to regenerate it."
    )


@pytest.mark.parametrize("component", generator.component_classes(), ids=lambda cls: cls.__name__)
def test_signature_covers_every_field(component: type[BaseModel]) -> None:
    parameters = {parameter.name for parameter in generator.signature(component)}

    # A plot also takes the bundles that stand for several of its fields at once.
    bundles = set(getattr(component, "option_bundles", {}))

    assert parameters == set(component.model_fields) | bundles
