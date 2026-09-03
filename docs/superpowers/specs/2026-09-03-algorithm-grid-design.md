# Algorithm parameter grids and grouped plots

Date: 2026-09-03
Status: implemented on branch `feat/algorithm-variants`

## Problem

Comparing FlexQAOA pipeline variants at several layer counts means registering one
algorithm entry per combination. Today that is a hand-built dict comprehension plus
a mixin that reaches past the plotting API:

```python
ALGORITHMS: dict[str, tuple[str, int]] = {
    f"{prefix}_{reps}": (series, reps)
    for reps in (1, 2, 4, 6, 8)
    for series, prefix in (("QAOA", "qaoa"), ("FlexQAOA", "flex_qaoa"))
}
```

Two distinct problems sit behind that.

**Registration.** The variants differ by nested pipeline settings, so the script
carries a `PLAIN` override dict and branches on `series == "FlexQAOA"` to decide
whether to apply it. Adding a third or fourth variant multiplies the branching.

**Grouping.** `luna_bench` groups bars by model, by algorithm, by a feature, or by a
*numeric* algorithm setting (`ParameterDimension._settings` rejects anything that is
not `int`/`float`, and reads flat attributes only via `getattr`). "Which pipeline
this is" is none of those, so the current script injects `x` and `hue` columns
directly in a `Grouped.create` override.

These are two ends of one problem: nothing records which axis values produced a
given algorithm entry. The registration side is what should record it, and the
plotting side is what should consume it.

## Part A - variant generators

Variants are passed to the existing `add_algorithm` as `variants`, a strategy object
rather than keyword arguments. It accepts either a `ParameterGrid` or a plain
`list[dict]` of complete configurations:

```python
XY = "pipeline.xy_mixer.enable"

grid = bench.add_algorithm(
    "flex_qaoa",
    FlexQAOA(                                          # the default version
        backend=AqariosGpu(),
        pipeline=PipelineParams(
            xy_mixer=XYMixerConfig(enable=False),
            indicator_function=IndicatorFunctionConfig(enable=False),
        ),
    ),
    variants=ParameterGrid({
        "reps": [1, 2, 4, 6, 8],
        XY: [False, True],
    }),
)
```

Ten entries: the cartesian product of the axes, each a deep copy of the base instance
with one combination applied.

### Why a strategy object rather than keyword arguments

**Keyword arguments collide with the method's own parameters.** `name=[...]` is
ambiguous - an axis, or the naming template? So is any future option. A strategy
object shares no namespace with the signature.

**The combinatorics are named at the call site.** `ParameterGrid` says "every
combination" the way `sklearn.model_selection.ParameterGrid` does, so the reader does
not infer it from `**kwargs` semantics. For GPU-backed QAOA runs the difference
between ten and forty executions is time and money, and it should be legible in the
call.

**Other strategies become expressible** without touching `add_algorithm` - the point
of the seam.

### The generator protocol

```python
class VariantGenerator(Protocol):
    def __iter__(self) -> Iterator[dict[str, Any]]: ...
    def __len__(self) -> int: ...
```

A generator yields **parameter dictionaries** and never sees the algorithm, exactly as
sklearn's does. That keeps it pure, inspectable and testable on its own -
`len(ParameterGrid({...}))` answers "how many runs am I committing to" before anything
is registered - and it puts deep-copying, path resolution and naming in one place
rather than in every strategy.

The cost of that purity is that a generator cannot check its paths against the model,
so `add_algorithm` validates **every** path against the base instance and raises
before registering anything. A typo like `pipeline.xy_mixr.enable` therefore fails
immediately rather than after ten benchmark runs.

### `ParameterGrid`

Takes a dict, or a list of dicts:

- `ParameterGrid({"reps": [2, 4], XY: [False, True]})` - four combinations.
- `ParameterGrid([{"reps": [2, 4]}, {"reps": [6], XY: [True]}])` - the union of two
  grids, three combinations.

The list form is how a partial space is expressed, which matters when combinations are
not all meaningful - an indicator-function setting for a run whose XY mixer is off,
say. It comes free with the sklearn semantics, so no separate filtering mechanism is
needed to start.

### The direct form, and the two meanings of `list[dict]`

A bare list bypasses the generator and states the configurations outright:

```python
bench.add_algorithm(
    "flex_qaoa",
    FlexQAOA(backend=AqariosGpu()),
    variants=[
        {"reps": 2, XY: False},      # one configuration
        {"reps": 6, XY: True},       # another
    ],
)
```

Two configurations, exactly as written - no product taken.

**`list[dict]` therefore means two different things depending on the wrapper, and the
values invert:**

| Form | Each dict is | Values are |
|---|---|---|
| `ParameterGrid([{...}, {...}])` | a grid, unioned with the others | **sequences** to cross |
| `variants=[{...}, {...}]` | one complete configuration | **scalars**, applied verbatim |

So `ParameterGrid([{"reps": [2, 4]}])` is two configurations, while
`variants=[{"reps": [2, 4]}]` is one configuration that tries to set `reps`
to the list `[2, 4]`.

That second case is a mistake, and **the re-validation step already catches it** -
`reps` is annotated `int`, so `model_validate` raises a `ValidationError` naming the
field. The guard is free, which is why the direct form applies values verbatim rather
than rejecting sequences: fields whose value genuinely *is* a list, such as the Scipy
optimizer's `bounds` and `options`, have to keep working.

`add_algorithm` normalises a bare list into a `ParameterList` generator on the way in,
so everything downstream - path validation, deep-copying, naming, the axes map - has
one code path regardless of which form was used.

The two forms are told apart by `isinstance(variants, Sequence)`, **not** by the
generator protocol: a `list` is iterable and sized, so it satisfies
`VariantGenerator` too and a protocol check would route the direct form down the
generator path.

### Later strategies

`ParameterGrid` and `ParameterList` ship. The protocol is what admits others - paired
rather than crossed axes, or a random sample of a large space - and they can be added
without changing `add_algorithm`.

### Value semantics

**Inside `ParameterGrid`, every axis value must be a sequence, and `str`, `bytes` and
`Mapping` do not count.** This is the one trap in the rule: `str` is iterable, so
`{"param_conversion": "basic"}` would otherwise expand silently into five
combinations, one per character. A value that is not an accepted sequence raises and
names the fix, which is also the right error for a bare `PipelineParams` passed
without a list around it.

- `range(1, 5)` is materialised with `list()`.
- An empty sequence yields zero combinations, which is always a mistake, and raises.

The direct form applies no such rule - see above.

**Dotted paths address nested model fields.** Applying one is `model_copy(deep=True)`,
then walk to the parent model, then set the leaf to a value validated against that
field's own annotation with a `TypeAdapter`.

The obvious alternative - rebuild the whole algorithm with
`model_validate(model_dump())`, as `LunaAlgorithmWrapper.wrap` does - is **wrong here,
and silently so**:

```python
>>> FlexQAOA.model_validate(FlexQAOA(backend=AqariosGpu()).model_dump()).backend
None
```

A backend does not survive a dump, which is exactly why `wrap` re-assigns
`x.backend = algorithm.backend` afterwards. Rebuilding per variant would have sent
every run to the default backend without a word. Validating just the leaf keeps the
backend and still rejects a value of the wrong type - which is what catches a grid
written into the direct form, where `reps` is annotated `int`.

`tests/unit/components/algorithms/test_variants.py::TestApplyParametersKeepsWhatADumpWouldLose`
pins this.

**Anything not named as an axis** keeps the base instance's value, so the current
`PLAIN` / `{}` branch in the script becomes one axis rather than two code paths.

**Per-entry registration reuses the existing `add_algorithm` path**, including its
`DataNotUniqueError` branch that warns and returns the existing entry, so re-running
the script stays safe as the script comments already rely on.

### Naming

The `name` argument becomes a prefix, and each entry gets a deterministic suffix
built from its parameter dictionary, keeping the **full** dotted path so two axes
sharing a leaf name (`pipeline.xy_mixer.enable` and
`pipeline.indicator_function.enable` both end in `enable`) cannot collide:

```
flex_qaoa[reps=4,pipeline.xy_mixer.enable=True]
```

Once Part B supplies display labels the entry name no longer reaches a figure - plots
read labels off the grid rather than parsing names - so the name only has to be unique
and stable, not pretty.

### Signature and return type

This is the one wrinkle in reusing `add_algorithm`: with variants it registers N
entries, so it cannot return a single `AlgorithmEntity`. Typed with `@overload`, for
which `luna_bench/custom/decorators/plot.py` is the in-repo precedent:

```python
@overload
def add_algorithm(self, name: str, algorithm: ...) -> AlgorithmEntity: ...
@overload
def add_algorithm(self, name: str, algorithm: ..., *,
                  variants: Variants) -> AlgorithmGrid: ...

#: What `variants` accepts.
type Variants = VariantGenerator | list[dict[str, Any]]
```

`AlgorithmGrid` carries:

- `entities: list[AlgorithmEntity]`
- `axes: dict[str, dict[str, Any]]` - axis name to (entry name to that axis' value)
- `axis(name, labels=None, title=None) -> GridDimension` - the axis as a plotting dimension (Part B)

`labels` maps an axis value to its display label, defaulting to `str(value)`. It is
needed because a nested toggle axis is declared as `{XY: [False, True]}`, so its
values are `False` and `True`, and a legend reading "False / True" is worse than one
reading "plain QAOA / XY mixer". Labelling belongs at the plot rather than on the
generator because it is a display concern - the same grid can be labelled two ways in
two figures, and the entry names in the database stay untouched either way.

`title` does the same for the axis label itself: a dotted path identifies an axis well
and labels one badly, so `title="Pipeline"` replaces `pipeline.xy_mixer.enable` under
the row of bars.

## Part B - `GridDimension` (conditional on the scope decision below)

A `Dimension` subclass in `luna_bench/plots/dimensions.py`, added to the
discriminated `Dimension` union with `kind: Literal["grid"]`. It holds a plain
`dict[str, str]` mapping algorithm name to display label, and `resolve` tags each row
with the label of its algorithm - the same shape of work `FeatureDimension.resolve`
already does per model.

It keeps **only** the grid's own algorithms, filtering the rest out of the rows the way
`ParameterDimension._resolve` does. That was not the first choice: mirroring
`FeatureDimension`, non-grid algorithms were initially bucketed under
`UNGROUPED_LABEL`. Rendering the showcase figure showed why that is wrong - a `scip`
baseline and two hand-picked variants landed in one `unknown` bar, which is the mean of
unrelated runs, and `unknown` also appeared as an entry in the *reps* legend.

The distinction is what the axis is per: `FeatureDimension` is per-model, where every
model deserves a bar and "unknown" honestly means "no category assigned".
A grid axis is per-algorithm, and a baseline has no value on it at all -
`ParameterDimension` already says exactly this ("a classical baseline in the same
benchmark has no place on that axis").

Plot configuration is persisted with the benchmark (see the comment on
`FeatureDimension._serialize_feature`), so a dimension has to survive a round trip
through the database. A `dict[str, str]` is JSON already, so unlike `FeatureDimension`
this needs no registry lookup to rebuild.

With it, the script's `Grouped` mixin and `_laid_out` factory both go away:

```python
XY = "pipeline.xy_mixer.enable"

bench.add_plot("avg_approximation", ApproximationRatioPlot(
    x=grid.axis(XY, labels={False: "plain QAOA", True: "XY mixer"}),
    grouping=grid.axis("reps"),
))
```

An axis is addressed by the keyword that declared it, so a dotted axis is addressed
by its dotted path.

and, because `ParameterSweepPlot.grouping` already accepts any `Dimension`, the same
axis works there:

```python
bench.add_plot("approximation_vs_reps", ApproximationRatioVsParameterPlot(
    x=ParameterDimension("reps"),
    grouping=grid.axis(XY, labels={False: "plain QAOA", True: "XY mixer"}),
))
```

## Part C - percent labels

Two plot titles say `(1.0 = optimal)` while their own y-axis is scaled to percent
(`scale=PERCENT`, `"Approximation Ratio [%]"`) and their reference line is already
labelled `Optimal (100%)`:

- `luna_bench/plots/performance/approximation_ratio_plot.py:52`
- `luna_bench/plots/analysis/metric_vs_parameter_plot.py:56`

Both become `(100% = optimal)`, which is the convention the sibling plots already
follow - `best_solution_found_ratio_plot.py:46` and
`fraction_of_overall_best_solution_plot.py:48` both say `(100% = optimal)` today. So
this aligns two outliers rather than introducing a phrasing.

Each string also appears a second time inside the file's `TYPE_CHECKING` block
(`:71` and `:76`). Those blocks are generated - "do not edit by hand" - so the change
is made to the real field and `scripts/type_hints.py` is re-run.

Not changed: `feasibility_ratio_plot.py:25` says "``1.0`` means every sample was
feasible". That is prose about what the *metric* returns, and the metric does return a
0-1 ratio; only the axis is scaled.

## Plot layout guidance

Independent of the code, the current layout has the two variables the wrong way round
for more than two variants.

`reps` is **ordinal** - reordering `1, 2, 4, 6, 8` changes the meaning - so it takes
one hue with monotone lightness steps. The pipeline variants are **nominal**.

The current script sets `x=LAYERS_COLUMN, hue=SERIES_LABEL`, putting the nominal
variable on the colour channel. `BarPlot._color_kwargs` (`bar_plot.py:872`) then hands
that hue `LunaColours.palette(nunique)`, the blue -> sage -> yellow ramp. At two
variants this accidentally works, because the two ends of a ramp are maximally
separated. At four or five it is a sequential ramp doing a categorical job, and
adjacent variants collapse into each other.

Recommended instead:

- **variant on `x`** - position and a tick label carry identity, at no cost in colour
  budget. Nominal-on-hue would make direct labels mandatory at four series and hit the
  soft cap at five to six.
- **reps on `hue`** with a single-hue light-to-dark ramp, so the colour shows the
  order. `LunaColours.palette` takes `anchors`, and `gradient()` interpolates between
  them, so this stays inside the existing palette system.

Two supporting details:

- **Order should be explicit.** `order` and `hue_order` currently fall out of
  `_distinct(full, x)`, i.e. the order rows arrived, i.e. the order the dict
  comprehension registered them. `create` forwards `**kwargs` to `seaborn.barplot`
  after `_color_kwargs`, and `_categorical_order` uses `setdefault`, so an explicit
  `order=` / `hue_order=` wins. Passing them from the grid axes removes the implicit
  dependency on comprehension order.
- **Uneven spacing.** `reps = (1, 2, 4, 6, 8)` on a categorical axis draws 1->2 as
  wide as 6->8, which misstates the trend. `ParameterSweepPlot` puts the setting on a
  real numeric axis (`ParameterDimension.resolve_values`), so it is the honest figure
  for "does another layer buy anything". Worth adding alongside the bars, not instead
  of them - the bars answer "which variant wins", the sweep answers "does depth help".

### Out of scope

`ApproximationRatioVsVarNumberPlot.run` hardcodes `hue="algorithm"`
(`approximation_ratio_vs_var_number_plot.py:66`), and the current `Grouped` mixin only
applies to `BarPlot` subclasses, so these scatters already colour ten algorithms from
a sequential ramp and would get fifteen or more. Noted, not addressed here.

## Testing

Following the existing layout under `tests/unit/components/plots/` and
`tests/unit/components/`:

`ParameterGrid` on its own, with no algorithm and no benchmark - the point of keeping
it pure:

- Expansion: cartesian product size and contents; single-axis; multi-axis.
- `len()` matches the number of dicts yielded, and iterating twice yields the same
  combinations in the same order.
- List form: `ParameterGrid([{...}, {...}])` is the union of the two grids, including
  when they name different axes.
- Sequence rule: `str` rejected, `bytes` rejected, `Mapping` rejected, bare pydantic
  model rejected, `range` accepted, empty sequence raises.

Then the registration side:

- Path validation: an unknown path raises, and **nothing is registered** - the check
  runs over every combination before the first entry is added.
- Dotted paths: nested leaf set; base instance not mutated; validators run on the
  rebuilt model.
- Base defaults: fields not named as axes keep the base instance's values.
- Re-registration: a second identical call warns and returns existing entries.
- Return type: a call without `variants` still returns a single
  `AlgorithmEntity`; with one it returns an `AlgorithmGrid` whose `axes` map every
  entry to its values.
- Direct form: a bare `list[dict]` registers exactly those configurations, no product;
  a scalar-typed field given a sequence there raises `ValidationError` naming the
  field; a genuinely list-valued field such as the optimizer's `options` is accepted.
- Normalisation: the direct form and `ParameterList` produce identical entries, names
  and axes.
- `GridDimension`: `resolve` tags rows; round-trips through JSON with the plot config;
  serves as both `x` and `grouping`.
- Part C: the two titles read `(100% = optimal)`, and the generated `TYPE_CHECKING`
  mirrors match the fields.

## Where this was built

The main working tree does not import: `registry_container.py:10` imports
`luna_bench.custom.base_components.base_insight`, which does not exist, and
`registry_info.py:29` still requests `RegistryContainer.plot_registry`, which the same
uncommitted diff renamed to `insight_registry`. That in-progress plot -> insight rename
is untouched here.

So the work was done in a git worktree on branch `feat/algorithm-variants`, branched
from `2c7dbb1`, which imports cleanly. Merging it will have to account for the rename
once that lands - `GridDimension` is added to `plots/dimensions.py`, which the rename
does not appear to touch.

## Open decision

**Scope.** Part A alone leaves `Grouped` and `_laid_out` in the script, fed from
`grid.axes` instead of a hand-built dict, and the sweep plots still cannot split by
variant. Part A plus Part B retires both and makes the sweep grouping work.

Recommendation: both. The mixin exists only because nothing recorded the provenance,
and Part A is what starts recording it.

**What "choose which variations to use" means.** Two readings, and they build
differently:

1. *Choose the strategy* - grid now, other generators later behind the protocol. This
   is what the design above delivers, and `ParameterGrid`'s list form already covers
   partial spaces.
2. *Choose a subset of what a generator produced* - register the grid, then select
   from it, e.g. a `filter=` predicate on `add_algorithm` or a filtering method on the
   generator.

Reading 1 is assumed here. Reading 2 is a real addition and worth saying so if it is
what was meant.
