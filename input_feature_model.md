# Generic model-lookup feature for luna-bench

**Target repo:** `luna-bench` (main)
**Status:** design approved, ready to implement. All code below was prototyped and verified against the installed `luna-bench` package — see [Verification already performed](#verification-already-performed).

---

## Problem

Some model properties cannot be derived from the model itself. A problem category
(`graph`, `combinatorial`, `scheduling`), a source dataset, a difficulty rating, a
known optimum — these are assigned externally, but they still need to reach metrics
and plots through the same channel as computed features.

Today the only example of this pattern is `PreCompOptSolFeature` in `luna-bench-lab`,
which hand-rolls a model→value lookup for one specific value type (a float objective).
Every new "attach a value to a model" feature would repeat that machinery.

## Scope

Add a generic base class to luna-bench main so that a concrete lookup feature is
one class body with nothing in it:

```python
@feature
class ProblemCategoryFeature(ValueLookupFeature[ProblemCategory]):
    """Maps each model to a hand-assigned problem category."""
```

The type parameter fixes the value type, drives pydantic validation, and determines
the result type — no per-subtype boilerplate.

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Lookup key** | `hash(model)` (int) | Already what luna-bench stores as `ModelMetadataEntity.hash` (see `_internal/usecases/modelset/model/model_add.py`, which calls `model.__hash__()`). Verified: stable across `encode()`/`decode()`, sensitive to both contents *and* name. No new hashing code needed in main. |
| **Miss policy** | Raise `ModelLookupMissError` | Strict by default. A mapping gap is a configuration mistake and should be loud. Overridable via `on_miss()` for subtypes that can derive the value. |
| **Mapping input** | `feature.add_model(model, value)` builder | Mirrors the `modelset.add(model)` flow; the user never hashes by hand, so keys cannot drift from their models. Returns `self` for chaining. |
| **Result type** | Second type parameter | Lets `PreCompOptSolFeature` (whose result carries `pre_terminated`/`runtime`, not a bare `value`) subclass the same base. `ValueLookupFeature` specializes it for the common case. |

### Why a miss is safe to raise

`FeatureRunUcImpl._run` (in `_internal/usecases/benchmark/feature/feature_run.py`)
wraps `feature.feature.run(model)` in a `try/except Exception` and records
`JobStatus.FAILED` with the error string for *that model only*. A raise therefore
surfaces as a failed feature result, not an aborted benchmark.

---

## Files to add / change

| Path | Change |
|---|---|
| `luna_bench/features/model_lookup.py` | **New.** The module below. |
| `luna_bench/features/__init__.py` | Export `LookupFeatureResult`, `ModelLookupFeature`, `ModelLookupMissError`, `ValueLookupFeature`. |
| `tests/.../test_model_lookup.py` | **New.** See [Tests to write](#tests-to-write). |
| `docs/features.md` | Add a short section; the class docstrings carry the detail. |

Do **not** register the base classes with `@feature` — they are abstract. Only
concrete subtypes get the decorator.

---

## The module

`luna_bench/features/model_lookup.py`:

```python
"""Features that serve a value looked up per model rather than computed from it.

Some model properties cannot be derived from the model itself — a problem
category ("graph", "scheduling"), a source dataset, a difficulty rating, a
known optimum. They are assigned externally and simply need to reach metrics
and plots alongside computed features.

:class:`ModelLookupFeature` is the generic base for that: a mapping from
``hash(model)`` to a value of the subtype's choosing. Subclasses fix the value
type (and, if needed, the result type) via type parameters, so a concrete
lookup feature is usually a class body with nothing in it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Self
from typing import TypeVar as _TypeVar

from pydantic import Field

from luna_bench.custom import BaseFeature, FeatureResult

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from luna_model import Model


class ModelLookupMissError(KeyError):
    """Raised when a model has no entry in a lookup feature's mapping.

    Attributes
    ----------
    model_name : str
        Name of the model that was not found.
    model_key : int
        The ``hash(model)`` that was looked up.
    feature_name : str
        Name of the lookup feature class that raised.
    """

    def __init__(self, model: Model, feature_cls: type) -> None:
        self.model_name = model.name
        self.model_key = hash(model)
        self.feature_name = feature_cls.__name__
        super().__init__(
            f"{feature_cls.__name__} has no entry for model {model.name!r} (key {hash(model)}). "
            f"Register it with .add_model(model, value) before passing the feature to Benchmark.add_feature()."
        )


class LookupFeatureResult[TValue](FeatureResult):
    """Result of a :class:`ValueLookupFeature`: the value assigned to the model.

    Attributes
    ----------
    value : TValue
        The value registered for this model. Its type is fixed by the concrete
        feature subclass, which also validates it.
    """

    value: TValue


class ModelLookupFeature[TValue, TResult: FeatureResult](BaseFeature[TResult], ABC):
    """Base for features whose value is assigned per model instead of computed.

    The mapping is keyed by ``hash(model)``, the same structural hash luna-bench
    already stores as :attr:`ModelMetadataEntity.hash`. It is stable across the
    ``encode()``/``decode()`` round-trip a benchmark performs before running
    features, and it covers the model's name as well as its contents, so models
    that differ in either get distinct keys.

    A miss raises :class:`ModelLookupMissError`. Subclasses that can derive the
    value themselves override :meth:`on_miss` — that is the hook
    ``PreCompOptSolFeature`` uses to fall back to solving.

    Attributes
    ----------
    mapping : dict[int, TValue]
        ``hash(model)`` to assigned value. Populate it with :meth:`add_model`
        rather than by hand, so keys can never drift from their models.

    Notes
    -----
    Populate the feature *before* handing it to ``Benchmark.add_feature()``.
    The benchmark serializes the feature's configuration at that point and
    reconstructs it from the database when the run happens, so entries added to
    the in-memory object afterwards never reach the run.
    """

    mapping: dict[int, TValue] = Field(default_factory=dict)

    def add_model(self, model: Model, value: TValue) -> Self:
        """Register ``value`` for ``model``, replacing any existing entry.

        Parameters
        ----------
        model : Model
            The model to assign a value to.
        value : TValue
            The value to serve whenever this model is seen.

        Returns
        -------
        Self
            The feature itself, so calls can be chained.
        """
        self.mapping[hash(model)] = value
        return self

    def add_models(self, entries: Mapping[Model, TValue] | Iterable[tuple[Model, TValue]]) -> Self:
        """Register several models at once.

        Parameters
        ----------
        entries : Mapping[Model, TValue] | Iterable[tuple[Model, TValue]]
            Model/value pairs, either as a mapping or as an iterable of tuples.

        Returns
        -------
        Self
            The feature itself, so calls can be chained.
        """
        pairs = entries.items() if hasattr(entries, "items") else entries
        for model, value in pairs:
            self.add_model(model, value)
        return self

    def covers(self, model: Model) -> bool:
        """Return whether ``model`` has an entry, without running the feature.

        Useful for validating a mapping against a modelset up front instead of
        discovering gaps as failed feature results mid-run.
        """
        return hash(model) in self.mapping

    def run(self, model: Model) -> TResult:
        """Return the registered value for ``model``.

        Parameters
        ----------
        model : Model
            The model to look up.

        Returns
        -------
        TResult
            The registered value, wrapped by :meth:`to_result`.

        Raises
        ------
        ModelLookupMissError
            If the model has no entry and :meth:`on_miss` is not overridden.
        """
        key = hash(model)
        if key not in self.mapping:
            return self.on_miss(model)
        return self.to_result(self.mapping[key], model)

    @abstractmethod
    def to_result(self, value: TValue, model: Model) -> TResult:
        """Wrap a looked-up ``value`` in this feature's result type."""

    def on_miss(self, model: Model) -> TResult:
        """Handle a model with no entry. Raises by default; override to compute one.

        Raises
        ------
        ModelLookupMissError
            Always, unless a subclass overrides this method.
        """
        raise ModelLookupMissError(model, type(self))


class ValueLookupFeature[TValue](ModelLookupFeature[TValue, LookupFeatureResult[TValue]], ABC):
    """A :class:`ModelLookupFeature` that reports its value as-is.

    This is the base to reach for. A concrete feature only names its value type;
    the result type is derived from it automatically, so
    ``ProblemCategoryFeature`` below yields ``LookupFeatureResult[ProblemCategory]``
    and validates against that enum on both input and output.

    Examples
    --------
    >>> @feature
    ... class DifficultyFeature(ValueLookupFeature[int]):
    ...     '''Hand-assigned difficulty rating per model.'''
    >>> f = DifficultyFeature().add_model(model, 3)
    >>> f.run(model).value
    3
    """

    result_cls: ClassVar[Any] = LookupFeatureResult

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Bind ``result_cls`` to ``LookupFeatureResult[<concrete value type>]``.

        Walks the MRO for the nearest base parametrized with a concrete type —
        pydantic records each parametrization in ``__pydantic_generic_metadata__``
        — so subclasses get a validating, self-describing result type for free.
        """
        super().__pydantic_init_subclass__(**kwargs)
        for base in cls.__mro__:
            args = getattr(base, "__pydantic_generic_metadata__", {}).get("args", ())
            if len(args) == 1 and not isinstance(args[0], _TypeVar):
                cls.result_cls = LookupFeatureResult[args[0]]
                return

    def to_result(self, value: TValue, model: Model) -> LookupFeatureResult[TValue]:  # noqa: ARG002
        """Wrap ``value`` in this subclass's parametrized result type."""
        return type(self).result_cls(value=value)
```

### Note on `__pydantic_init_subclass__`

This is the one non-obvious part, and it is load-bearing. Without it,
`to_result` would build `LookupFeatureResult[TValue]` with the *unbound* type
variable, giving every subtype the same unvalidated result class (observed as
`LookupFeatureResult[TypeVar]`). Pydantic creates an intermediate class per
parametrization and records the concrete argument in
`__pydantic_generic_metadata__`, so walking the MRO recovers it.

`__pydantic_init_subclass__` is used rather than `__init_subclass__` because it
runs after pydantic has finished building the class. `__init_subclass__` fires
before the parametrization metadata is available, and fires twice per subclass.

---

## Example subtype

The category enum is a **caller-side concern** — luna-bench should ship the
machinery, not a fixed taxonomy. Ship this as a documented example (or in
`luna-bench-lab`), not as a core class, unless a canonical taxonomy is wanted:

```python
from enum import StrEnum

from luna_bench.custom import feature
from luna_bench.features import ValueLookupFeature


class ProblemCategory(StrEnum):
    """Coarse problem family a model belongs to."""

    GRAPH = "graph"
    COMBINATORIAL = "combinatorial"
    SCHEDULING = "scheduling"
    ROUTING = "routing"


@feature
class ProblemCategoryFeature(ValueLookupFeature[ProblemCategory]):
    """Maps each model to a hand-assigned problem category."""
```

`StrEnum` is a good default value type: it validates on input, serializes to a
plain JSON string, and reads well in plot legends. Any JSON-serializable type
works — `int`, `str`, a `BaseModel`, a tuple.

---

## Usage

```python
categories = ProblemCategoryFeature()

modelset.add(max_cut_model)
categories.add_model(max_cut_model, ProblemCategory.GRAPH)

modelset.add(knapsack_model)
categories.add_model(knapsack_model, ProblemCategory.COMBINATORIAL)

# Chaining and bulk registration both work:
categories.add_models({tsp_model: ProblemCategory.ROUTING})

bench.add_feature(name="category", feature=categories)   # populate BEFORE this call
```

Optional pre-flight check, better than discovering gaps as failed results:

```python
missing = [m.name for m in modelset.models if not categories.covers(m.model)]
if missing:
    raise ValueError(f"No category assigned for: {missing}")
```

---

## Consuming the value in metrics and plots

Feature results are keyed by the **feature class**, so a concrete subtype is
required (a parametrized alias like `ValueLookupFeature[ProblemCategory]` is not
a usable key). This is the main reason the design uses subclasses rather than
bare parametrization.

```python
@metric(ProblemCategoryFeature)
class CategoryTaggedRatio(BaseMetric[SomeResult]):
    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> SomeResult:
        category = feature_results.first(ProblemCategoryFeature).value
        ...
```

`FeatureResultContainer.first` / `.get` / `.get_all` all work unchanged.

---

## Persistence and lifecycle

Verified behaviours worth knowing before implementing:

1. **JSON round-trip is safe despite `int` keys.** JSON object keys are strings;
   pydantic serializes `dict[int, TValue]` with string keys and coerces them back
   to `int` on validation. Verified: `mapping` compares equal after
   `model_dump_json()` → `model_validate_json()`, with `int` keys restored.
2. **Populate before `add_feature`.** The runner reconstructs the feature from
   `config_data` in the database (`FeatureRunUcImpl`), so post-add mutation of the
   in-memory object is lost.
3. **Re-adding a feature name does not update it.** `Benchmark.add_feature` catches
   `DataNotUniqueError`, logs `"Loading existing feature"`, and returns the
   *existing* feature. Changing a mapping and re-adding under the same name
   silently keeps the old mapping — use a new name or remove the feature first.
4. **Hash collisions.** `hash(model)` covers contents and name. Two genuinely
   identical models with the same name collide, which is the desired behaviour
   (they are the same instance); a modelset rejects duplicate names anyway.

---

## Optional follow-up: fold `PreCompOptSolFeature` onto this base

Not required for the initial change, but it is what the two type parameters buy.
The current implementation in `luna-bench-lab` (`luna_bench_lab/features/pre_comp_opt.py`)
becomes:

```python
@feature
class PreCompOptSolFeature(ModelLookupFeature[tuple[float, bool], OptSolFeatureResult]):
    """Known optimum per model, falling back to solving on a miss."""

    max_runtime: float | None = None
    quiet_output: bool = True

    def to_result(self, value: tuple[float, bool], model: Model) -> OptSolFeatureResult:
        objective, pre_terminated = value
        return OptSolFeatureResult(global_best_sol=objective, pre_terminated=pre_terminated, runtime=0.0)

    def on_miss(self, model: Model) -> OptSolFeatureResult:
        return OptSolFeature(max_runtime=self.max_runtime, quiet_output=self.quiet_output).run(model)
```

This drops `PreCompSolution` and the lab-local `model_hash()` (sha256 of
name + `hash(model)`) in favour of `hash(model)`. **This is a breaking change to
persisted lab data** — existing `PreCompSolution` records key on the sha256 digest.
Treat it as a separate, deliberate migration, and consider a
`(float, bool)` → named-model swap for readability if the tuple proves awkward.

---

## Tests to write

Mirror the structure of `tests/unit/features/test_precomp_opt.py`. All of these
were exercised in the prototype and pass:

- `add_model` / chained `add_model` / `add_models` (mapping and iterable forms)
- Value is returned for a registered model; `covers()` is `True`/`False` correctly
- A miss raises `ModelLookupMissError` carrying `model_name` and `feature_name`
- A model that has been through `encode()`/`decode()` still hits
- `model_dump_json()` → `model_validate_json()` preserves the mapping with `int`
  keys, and the reconstructed feature still resolves
- An invalid value for the concrete type parameter raises `ValidationError`
- Two subtypes (`ValueLookupFeature[int]`, `ValueLookupFeature[SomeEnum]`) get
  distinct, correctly parametrized `result_cls` values — no cross-contamination
- A `ModelLookupFeature` subtype with a custom result type and an overridden
  `on_miss` returns the fallback instead of raising
- The abstract base cannot be instantiated

---

## Verification already performed

Prototyped against `luna-bench` as installed in `luna-bench-lab`'s venv
(Python 3.14, pydantic v2). Confirmed:

- PEP 695 generics compose with `BaseFeature`, `RegisteredClassMeta`, and pydantic;
  `@feature` registers a generic subclass and `registered_id` resolves normally.
- The concrete type parameter drives real validation — a bad enum value raises
  `ValidationError`.
- `hash(model)`: name-sensitive, content-sensitive, stable across `encode()`/`decode()`.
- `int`-keyed mapping survives the JSON round trip.
- The two-parameter form supports a custom result type with an overriding `on_miss`.
- The module passes `ruff check` under `luna-bench-lab`'s config (numpydoc `D`,
  `ANN`, `TCH`, 120 cols). **Import order differs between repos:** in luna-bench
  main, `pydantic` belongs in the third-party block and `luna_bench` in the
  first-party block (as written above); in luna-bench-lab both are third-party and
  `luna_bench` sorts first.

17/17 prototype assertions passed.

---

## Non-goals

- No default/fallback value on a miss — strict raise, with `on_miss` as the
  documented escape hatch.
- No taxonomy shipped in core (`ProblemCategory` is an example).
- No loading of mappings from files or registries; `add_model` covers the current
  need. A `from_json()` classmethod is trivial to add later if mappings grow.
