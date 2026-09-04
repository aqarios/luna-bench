"""How one algorithm becomes many: the strategies that generate parameter variants.

A benchmark that asks "does another QAOA layer buy anything, and does it buy more with
the XY mixer on" needs one algorithm entry per combination. The combinations are a
statement of their own - a full cross of two axes is a very different number of runs
from a handful of hand-picked configurations - so they are named at the call site
rather than inferred from keyword arguments:

.. code-block:: python

    bench.add_algorithm(
        "flex_qaoa",
        FlexQAOA(backend=AqariosGpu()),
        variants=ParameterGrid({"reps": [1, 2, 4, 6, 8], "pipeline.xy_mixer.enable": [False, True]}),
    )

A generator yields **parameter dictionaries** and never sees the algorithm, the way
`sklearn.model_selection.ParameterGrid` does. That keeps it inspectable on its own -
``len(ParameterGrid(...))`` answers "how many runs am I committing to" before anything
is registered - and it leaves deep-copying, path resolution and naming in one place
instead of in every strategy.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel, TypeAdapter

from luna_bench.errors.components.algorithms.unknown_parameter_path_error import UnknownParameterPathError

if TYPE_CHECKING:
    from luna_bench.entities import AlgorithmEntity
    from luna_bench.plots.dimensions import GridDimension


@runtime_checkable
class VariantGenerator(Protocol):
    """What `Benchmark.add_algorithm` accepts as its ``variants``.

    A generator is iterable and sized: it yields one parameter dictionary per variant,
    and says how many there are without being iterated.
    """

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield one parameter dictionary per variant."""
        ...

    def __len__(self) -> int:
        """Return how many variants this generator yields."""
        ...


def _as_axis_values(axis: str, values: Any) -> list[Any]:  # noqa: ANN401
    """Return the values of one grid axis as a list, rejecting what cannot be one.

    Parameters
    ----------
    axis : str
        Name of the axis, for the error message.
    values : Any
        What the axis was given.

    Returns
    -------
    list[Any]
        The values, materialised so a ``range`` or other one-shot sequence can be
        crossed more than once.

    Raises
    ------
    TypeError
        If *values* is not a sequence, or is one of the sequences that is almost
        always a mistake here. ``str`` is the reason this check exists: it is
        iterable, so ``{"param_conversion": "basic"}`` would otherwise expand into
        five variants, one per character.
    ValueError
        If *values* is empty, which would silently yield no variants at all.
    """
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(values, Sequence):
        msg = (
            f"Axis '{axis}' of a ParameterGrid must be a sequence of values to cross, "
            f"got {type(values).__name__}. Wrap a single value in a list, e.g. [{values!r}]."
        )
        raise TypeError(msg)

    materialised = list(values)
    if not materialised:
        msg = f"Axis '{axis}' of a ParameterGrid is empty, so it would yield no variants at all."
        raise ValueError(msg)

    return materialised


class ParameterGrid:
    """Every combination of the given axes, as `sklearn.model_selection.ParameterGrid`.

    Each axis maps a parameter name - a plain field, or a dotted path into a nested
    configuration - to the sequence of values it takes. The variants are the full cross
    of the axes, with the last axis varying fastest and the axes kept in the order they
    were declared.

    A list of dicts is the union of that many grids, which is how a partial space is
    expressed: not every combination is always meaningful, and the union says which
    ones are without needing a separate filter.

    Parameters
    ----------
    param_grid : Mapping[str, Sequence[Any]] | Sequence[Mapping[str, Sequence[Any]]]
        The axes, or several sets of axes to union.

    Examples
    --------
    >>> len(ParameterGrid({"reps": [2, 4, 6], "shots": [1024, 4096]}))
    6
    >>> list(ParameterGrid([{"reps": [2]}, {"reps": [6], "shots": [4096]}]))
    [{'reps': 2}, {'reps': 6, 'shots': 4096}]

    See Also
    --------
    ParameterList : Complete configurations stated outright, with no product taken.
    """

    def __init__(self, param_grid: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> None:
        grids = [param_grid] if isinstance(param_grid, Mapping) else list(param_grid)

        self._grids: list[dict[str, list[Any]]] = [
            {axis: _as_axis_values(axis, values) for axis, values in grid.items()} for grid in grids
        ]

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield one parameter dictionary per combination.

        Yields
        ------
        dict[str, Any]
            Parameter name to value, one entry per axis of the grid it came from.
        """
        for grid in self._grids:
            axes = list(grid)
            for combination in product(*(grid[axis] for axis in axes)):
                yield dict(zip(axes, combination, strict=True))

    def __len__(self) -> int:
        """Return how many combinations the grid holds, without iterating it."""
        total = 0
        for grid in self._grids:
            size = 1
            for values in grid.values():
                size *= len(values)
            total += size
        return total


class ParameterList:
    """Complete configurations, stated outright - no product is taken.

    The counterpart of `ParameterGrid` for a space that is easier to write down than to
    describe. Each dictionary is one variant, and its values are applied as they are:
    unlike a grid axis a value here is never crossed, so a field whose value genuinely
    *is* a list keeps working.

    A sequence given here by mistake - ``{"reps": [2, 4]}``, meaning a grid - is caught
    when the variant is applied, since re-validating the algorithm rejects a list where
    its field is annotated ``int``.

    Parameters
    ----------
    configurations : Sequence[Mapping[str, Any]]
        One mapping of parameter name to value per variant.

    Examples
    --------
    >>> list(ParameterList([{"reps": 2}, {"reps": 6, "shots": 4096}]))
    [{'reps': 2}, {'reps': 6, 'shots': 4096}]

    See Also
    --------
    ParameterGrid : Every combination of a set of axes.
    """

    def __init__(self, configurations: Sequence[Mapping[str, Any]]) -> None:
        materialised = [dict(configuration) for configuration in configurations]
        if not materialised:
            msg = "A ParameterList is empty, so it would yield no variants at all."
            raise ValueError(msg)

        self._configurations = materialised

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield each configuration as it was given.

        Yields
        ------
        dict[str, Any]
            Parameter name to value, one entry per variant.
        """
        yield from (dict(configuration) for configuration in self._configurations)

    def __len__(self) -> int:
        """Return how many configurations were given."""
        return len(self._configurations)


#: What ``variants`` accepts: a generator, or a plain list of complete configurations.
type Variants = VariantGenerator | Sequence[Mapping[str, Any]]


def apply_parameters[T: BaseModel](algorithm: T, parameters: Mapping[str, Any]) -> T:
    """Return a copy of *algorithm* with one variant's parameters applied.

    A parameter is addressed by name, or by a dotted path into a nested configuration -
    ``"pipeline.xy_mixer.enable"`` reaches the block inside FlexQAOA's pipeline. The
    base is left as it was, so the same one can be varied any number of times.

    The value is validated against the field's own annotation before it is set, rather
    than by rebuilding the whole algorithm from a dump. That is not a shortcut: a dump
    does not round-trip a backend - ``FlexQAOA.model_validate(f.model_dump()).backend``
    is ``None`` however the original was configured, which is why
    `LunaAlgorithmWrapper.wrap` re-assigns it afterwards. Rebuilding here would send
    every variant to the default backend without saying so. Validating the leaf keeps
    the backend and still rejects a value of the wrong type, which is what catches a
    grid written into the direct form: ``{"reps": [2, 4]}`` where ``reps`` is an
    ``int``.

    Parameters
    ----------
    algorithm : T
        The default version every variant starts from. Not modified.
    parameters : Mapping[str, Any]
        Parameter name or dotted path to the value it takes in this variant.

    Returns
    -------
    T
        A deep copy of *algorithm* carrying the variant's parameters.

    Raises
    ------
    UnknownParameterPathError
        If a path names a field the algorithm does not have, or reaches through a field
        that is not itself a configuration.
    pydantic.ValidationError
        If a value does not fit the field it is set on.
    """
    varied = algorithm.model_copy(deep=True)
    name = type(algorithm).__name__

    for path, value in parameters.items():
        *ancestors, leaf = path.split(".")

        parent: Any = varied
        for step in ancestors:
            parent = _child(parent, step, path=path, algorithm_name=name)

        if not isinstance(parent, BaseModel) or leaf not in type(parent).model_fields:
            available = list(type(parent).model_fields) if isinstance(parent, BaseModel) else []
            raise UnknownParameterPathError(path, name, available)

        annotation = type(parent).model_fields[leaf].annotation
        setattr(parent, leaf, TypeAdapter(annotation).validate_python(value))

    return varied


def _child(parent: Any, step: str, *, path: str, algorithm_name: str) -> Any:  # noqa: ANN401
    """Return the configuration *step* names on *parent*, or say the path is wrong.

    Parameters
    ----------
    parent : Any
        The configuration the step is read off.
    step : str
        One segment of the dotted path.
    path : str
        The whole path, for the error message.
    algorithm_name : str
        Name of the algorithm class, for the error message.

    Returns
    -------
    Any
        The value of that field.

    Raises
    ------
    UnknownParameterPathError
        If *parent* is not a configuration, or has no such field.
    """
    if not isinstance(parent, BaseModel) or step not in type(parent).model_fields:
        available = list(type(parent).model_fields) if isinstance(parent, BaseModel) else []
        raise UnknownParameterPathError(path, algorithm_name, available)

    return getattr(parent, step)


@dataclass(frozen=True)
class AlgorithmGrid:
    """The algorithm entries one grid of variants registered, and what varied.

    Returned by `Benchmark.add_algorithm` when it is given ``variants``. It carries what
    the plots need that a list of entries does not: which value of which axis produced
    each entry, so a figure can group by "which pipeline this is" rather than by a name
    it would have to parse.

    Attributes
    ----------
    entities : list[AlgorithmEntity]
        The registered entries, in the order the generator yielded them.
    axes : dict[str, dict[str, Any]]
        Axis name to a mapping of entry name to the value that entry took on it. An
        entry is absent from an axis it was not varied along, which happens when a
        `ParameterGrid` unions grids that name different axes.
    """

    entities: list[AlgorithmEntity]
    axes: dict[str, dict[str, Any]]

    def axis(
        self,
        name: str,
        labels: Mapping[Any, str] | None = None,
        title: str | None = None,
    ) -> GridDimension:
        """Return one axis as a dimension a plot can put on an axis or give to the colours.

        Parameters
        ----------
        name : str
            The axis, named as the variant generator named it - a dotted path stays
            dotted.
        labels : Mapping[Any, str] | None, optional
            What each value is called on the figure, by default the value itself. This
            is where a nested toggle stops reading as ``True`` / ``False``: an axis
            declared as ``{"pipeline.xy_mixer.enable": [False, True]}`` has those for
            values, and a legend is better off saying "plain QAOA" and "XY mixer".
        title : str | None, optional
            What the axis or legend is called, by default the axis name. A dotted path
            identifies an axis well and labels one badly - ``"Pipeline"`` beats
            ``"pipeline.xy_mixer.enable"`` under a row of bars.

        Returns
        -------
        GridDimension
            The axis, ready to hand to a plot's ``x`` or ``grouping``.

        Raises
        ------
        KeyError
            If no axis of that name was varied.

        Examples
        --------
        >>> XY = "pipeline.xy_mixer.enable"
        >>> ApproximationRatioPlot(
        ...     x=grid.axis(XY, labels={False: "plain QAOA", True: "XY mixer"}, title="Pipeline"),
        ...     grouping=grid.axis("reps", title="Layers (reps)"),
        ... )
        """
        # Imported here because the plots are an optional extra: registering variants
        # must not require seaborn to be installed.
        from luna_bench.plots.dimensions import GridDimension  # noqa: PLC0415

        if name not in self.axes:
            msg = f"No axis {name!r} was varied. Varied axes: {', '.join(sorted(self.axes)) or 'none'}."
            raise KeyError(msg)

        chosen = labels or {}
        return GridDimension(
            labels={entry: str(chosen.get(value, value)) for entry, value in self.axes[name].items()},
            label=title if title is not None else name,
        )
