"""What a bar plot organises its data by, one class per kind of dimension.

A benchmark offers three quite different answers to "compared to what": another column of
the plotted data, a property assigned to a model, or the setting an algorithm was run
with. They need different data and behave differently - only the last one drops the
algorithms it does not apply to - so each is its own class.

The same dimension serves both roles a bar plot has for one, since both come down to
"which values stand next to each other": the bars themselves, and what splits each of them
into a group. Which role it plays is the field it is given to, not the class:

.. code-block:: python

    RuntimePlot(x=ModelDimension())  # a bar per instance
    RuntimePlot(grouping=ModelDimension())  # each bar split per instance
    RuntimePlot(grouping=FeatureDimension(UseCaseFeature))  # ... per use case
    RuntimePlot(x=AlgorithmDimension(), grouping=ParameterDimension("reps"))
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer, field_validator

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

    from luna_bench.custom import BenchmarkResultContainer
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
    from luna_bench.custom.types import FeatureClass

    #: Any feature class, whatever result type it produces - a grouper only reads an
    #: attribute off the result, so it has no reason to be picky about which one.
    type GroupFeature = FeatureClass[Any]
else:
    # Runtime-only fallback, as in ``luna_bench.custom.types``: kept concrete so pydantic
    # can resolve the annotation without the feature's own result type.
    type GroupFeature = type

#: Group used for models the grouping feature has no result for.
UNGROUPED_LABEL = "unknown"

#: Scale of a dimension read in percent, i.e. what a ratio of ``1.0`` is drawn as. Every
#: ratio a benchmark plots goes on the axis this way, so two of them can be read against
#: each other without checking which one is a share and which one a percentage.
PERCENT = 100.0

logger: Logger = logging.getLogger(__name__)


class BaseDimension(BaseModel, ABC):
    """Base of what a bar plot can organise its data by.

    A dimension makes sure the rows carry the values it stands for and says which column
    holds them; the plot then puts that column on the x-axis or gives it to the colours.
    Rows it cannot place are its own business - a model without a feature result becomes
    ``"unknown"``, an algorithm without the swept setting is left out entirely.

    Attributes
    ----------
    label : str | None
        What the axis or the legend is titled, by default the name of the dimension.
    default_label : ClassVar[str]
        The title used when none is given.
    """

    model_config = ConfigDict(extra="forbid")

    default_label: ClassVar[str] = ""

    label: str | None = None

    def __init__(self, label: str | None = None, /, **data: Any) -> None:
        """Take the title positionally, which is all a column dimension has to say.

        Parameters
        ----------
        label : str | None, optional
            What the axis or the legend is titled.
        **data : Any
            The remaining fields.
        """
        if label is not None:
            data["label"] = label
        super().__init__(**data)

    @property
    def title(self) -> str:
        """Return what the axis or legend this dimension is on is called."""
        return self.label or self.default_label

    @abstractmethod
    def resolve(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> str | None:
        """Make sure *rows* carry this dimension, and return the column that holds it.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data, for the dimensions that are not in the rows already.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated - and, where a dimension applies to only
            part of the data, reduced - in place.

        Returns
        -------
        str | None
            The column to plot by, or ``None`` when the dimension does not apply to this
            data - the bars then stay ungrouped, or keep the plot's own x-axis.
        """


class ColumnDimension(BaseDimension, ABC):
    """Groups along a column the rows already carry.

    Attributes
    ----------
    column : ClassVar[str]
        The column the subclass groups by.
    """

    column: ClassVar[str]

    def resolve(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> str | None:
        """Return the column this dimension stands for, which the rows carry already.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Unused; the column is in the rows already.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated in place when a title of its own renames the
            column.

        Returns
        -------
        str | None
            The column, or ``None`` when no row carries it.
        """
        _ = benchmark_results

        if not any(self.column in row for row in rows):
            logger.warning("No column '%s' in the plotted data", self.column)
            return None

        if self.label is not None and self.label != self.column:
            for row in rows:
                row[self.label] = row.get(self.column)
            return self.label

        return self.column


class ModelDimension(ColumnDimension):
    """Splits each bar per model, so an average cannot hide behind the easy instances.

    Examples
    --------
    >>> RuntimePlot(grouping=ModelDimension(label="Instance"))
    """

    kind: Literal["model"] = "model"
    column: ClassVar[str] = "model"
    default_label: ClassVar[str] = "Model"
    if TYPE_CHECKING:
        # --- generated by scripts/type_hints.py, do not edit by hand ---
        # Mirrors the pydantic fields so IDEs show every option on the constructor.
        # Never executed: pydantic builds the real ``__init__``.
        def __init__(
            self,
            *,
            label: str | None = None,
            kind: Literal["model"] = "model",
        ) -> None: ...


class AlgorithmDimension(ColumnDimension):
    """Splits each bar per algorithm, for a plot whose bars are something else.

    Examples
    --------
    >>> RuntimePerModelPlot(grouping=AlgorithmDimension())
    """

    kind: Literal["algorithm"] = "algorithm"
    column: ClassVar[str] = "algorithm"
    default_label: ClassVar[str] = "Algorithm"
    if TYPE_CHECKING:
        # --- generated by scripts/type_hints.py, do not edit by hand ---
        # Mirrors the pydantic fields so IDEs show every option on the constructor.
        # Never executed: pydantic builds the real ``__init__``.
        def __init__(
            self,
            *,
            label: str | None = None,
            kind: Literal["algorithm"] = "algorithm",
        ) -> None: ...


class FeatureDimension(BaseDimension):
    """Splits each bar along a value looked up per model.

    Typically a use case or problem category assigned with a lookup feature. Models the
    feature has no result for are grouped as ``"unknown"``; if no model has one, the plot
    falls back to ungrouped bars.

    Attributes
    ----------
    feature : GroupFeature
        The feature whose per-model value is the group.
    attribute : str
        Attribute read off the feature result, by default ``"value"`` - what the lookup
        features expose.

    Examples
    --------
    >>> RuntimePlot(grouping=FeatureDimension(feature=UseCaseFeature, label="Use case"))
    """

    kind: Literal["feature"] = "feature"
    feature: GroupFeature
    attribute: str = "value"

    def __init__(self, feature: GroupFeature | None = None, /, **data: Any) -> None:
        """Take the feature positionally, since it is what the dimension is.

        Parameters
        ----------
        feature : GroupFeature | None, optional
            The feature whose per-model value is the dimension.
        **data : Any
            The remaining fields.
        """
        if feature is not None:
            data["feature"] = feature
        super().__init__(**data)

    @field_serializer("feature")
    def _serialize_feature(self, value: GroupFeature) -> str:
        """Store the feature by id, since a class is not JSON.

        The plot configuration is persisted with the benchmark, so the feature has to
        survive a round trip through the database as the id it is registered under.
        """
        return getattr(value, "registered_id", None) or f"{value.__module__}.{value.__qualname__}"

    @field_validator("feature", mode="before")
    @classmethod
    def _resolve_feature(cls, value: Any) -> Any:  # noqa: ANN401
        """Turn the id a stored configuration carries back into the feature class."""
        if not isinstance(value, str):
            return value

        from luna_bench.custom.registry_info import RegistryInfo  # noqa: PLC0415

        return RegistryInfo.get_feature_by_id(value)

    @property
    def default_label(self) -> str:  # type: ignore[override]
        """Return the feature's name without its ``"Feature"`` suffix."""
        return self.feature.__name__.removesuffix("Feature")

    def resolve(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> str | None:
        """Tag every row with the value its model has for the feature.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the feature results are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated in place. Each row is expected to carry the
            model it belongs to under ``"model"``.

        Returns
        -------
        str | None
            The column the values were written to, or ``None`` when no model has a result.
        """
        values = {model_name: self._value(container) for model_name, container in benchmark_results.features.items()}

        if all(value is None for value in values.values()):
            logger.warning("No results for feature %s", self.feature.__name__)
            return None

        for row in rows:
            row[self.title] = values.get(str(row.get("model", ""))) or UNGROUPED_LABEL

        return self.title

    def _value(self, feature_results: FeatureResultContainer) -> str | None:
        """Read the group value of a single model, or ``None`` when it has none."""
        try:
            result = feature_results.first(self.feature)
        except Exception:  # A model without a result for the feature is simply ungrouped.
            return None

        value = getattr(result, self.attribute, None)
        return None if value is None else str(value)


class ParameterDimension(BaseDimension):
    """Splits each bar along a setting the algorithms were configured with.

    Only the algorithms that carry the setting are plotted: a sweep is a statement about
    one algorithm at several depths, and a classical baseline in the same benchmark has no
    place on that axis. The rows are ordered by the setting, so the groups read low to
    high.

    Attributes
    ----------
    parameter : str
        Attribute of the algorithm configuration, e.g. ``"reps"`` for the layer count of a
        QAOA. Any name, which is why it is a string where the others are a class or a
        column of their own.

    Examples
    --------
    >>> ApproximationRatioPlot(x="model", grouping=ParameterDimension(parameter="reps"))
    """

    kind: Literal["parameter"] = "parameter"
    parameter: str

    def __init__(self, parameter: str | None = None, /, **data: Any) -> None:
        """Take the parameter name positionally, since it is what the dimension is.

        Parameters
        ----------
        parameter : str | None, optional
            Attribute of the algorithm configuration that is swept.
        **data : Any
            The remaining fields.
        """
        if parameter is not None:
            data["parameter"] = parameter
        super().__init__(**data)

    @property
    def default_label(self) -> str:  # type: ignore[override]
        """Return the name of the swept parameter."""
        return self.parameter

    def resolve(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> str | None:
        """Keep the algorithms configured with the parameter, and name their group by it.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the algorithm configurations are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated and filtered in place.

        Returns
        -------
        str | None
            The column the settings were written to, or ``None`` when no algorithm carries
            the parameter.
        """
        return self._resolve(benchmark_results, rows, lambda setting: f"{self.parameter}={setting:g}")

    def resolve_values(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> str | None:
        """Keep those algorithms too, but tag them with the setting as the number it is.

        The counterpart of :meth:`resolve` for an axis that is continuous rather than a row
        of categories: a sweep is read off the *distance* between its points, so ``reps``
        of 1, 2 and 4 have to reach the axis as numbers and not as three equally wide
        labels. What the parameter is called is on the axis title either way.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the algorithm configurations are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated and filtered in place.

        Returns
        -------
        str | None
            The column the settings were written to, or ``None`` when no algorithm carries
            the parameter.
        """
        return self._resolve(benchmark_results, rows, float)

    def _resolve(
        self,
        benchmark_results: BenchmarkResultContainer,
        rows: list[dict[str, Any]],
        as_value: Callable[[float], Any],
    ) -> str | None:
        """Filter the rows to the algorithms carrying the parameter and tag them with it.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the algorithm configurations are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated and filtered in place.
        as_value : Callable[[float], Any]
            What a setting is written to the row as - its own number, or a label naming it.

        Returns
        -------
        str | None
            The column the settings were written to, or ``None`` when no algorithm carries
            the parameter.
        """
        settings = self._settings(benchmark_results)
        kept = [row for row in rows if row.get("algorithm") in settings]

        if not kept:
            logger.warning("No algorithm was configured with '%s'", self.parameter)
            return None

        kept.sort(key=lambda row: settings[row["algorithm"]])
        rows[:] = kept

        for row in rows:
            row[self.title] = as_value(settings[row["algorithm"]])

        return self.title

    def _settings(self, benchmark_results: BenchmarkResultContainer) -> dict[str, float]:
        """Return the value of the parameter per algorithm that was configured with one.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the algorithm configurations are read from.

        Returns
        -------
        dict[str, float]
            Algorithm name to setting, for the algorithms that have a numeric one.
        """
        settings: dict[str, float] = {}
        for runs in benchmark_results.algorithms.values():
            for algorithm_name, run in runs.items():
                value = getattr(run.algorithm, self.parameter, None)
                # A bool is an int in Python, but not a setting a group reads as a number.
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                settings[algorithm_name] = float(value)
        return settings


class GridDimension(BaseDimension):
    """Splits the data along one axis of a grid of algorithm variants.

    The dimension `AlgorithmGrid.axis` hands back. A benchmark that runs the same
    algorithm at several depths and with several pipelines has a two-dimensional space
    of entries, and neither of its axes is something the other dimensions can express:
    an algorithm name is one entry rather than an axis, and a `ParameterDimension`
    reads a single numeric field, so "which pipeline this is" - a nested toggle, or a
    whole configuration object - is none of them.

    So the grid says it instead. It knows which value of which axis produced each
    entry, and this carries that down to the figure as a label per algorithm.

    Attributes
    ----------
    labels : dict[str, str]
        Algorithm name to the label of the value it took on this axis. A plain mapping
        of strings, which is what lets a stored plot configuration round-trip through
        the database without a registry lookup.

    Examples
    --------
    >>> grid = bench.add_algorithm("fq", FlexQAOA(), variants=ParameterGrid({"reps": [2, 4, 6]}))
    >>> ApproximationRatioPlot(x=grid.axis("reps"))
    """

    kind: Literal["grid"] = "grid"
    labels: dict[str, str] = {}  # pydantic copies a mutable default per instance.
    default_label: ClassVar[str] = "Variant"

    if TYPE_CHECKING:
        # --- generated by scripts/type_hints.py, do not edit by hand ---
        # Mirrors the pydantic fields so IDEs show every option on the constructor.
        # Never executed: pydantic builds the real ``__init__``.
        def __init__(
            self,
            *,
            label: str | None = None,
            kind: Literal["grid"] = "grid",
            labels: dict[str, str] = {},  # noqa: B006
        ) -> None: ...

    def resolve(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> str | None:
        """Tag every row with the label its algorithm has on this axis.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Unused; the grid recorded what varied when the algorithms were registered,
            so nothing has to be read back off the results.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated in place. Each row is expected to carry
            the algorithm it belongs to under ``"algorithm"``.

        Returns
        -------
        str | None
            The column the labels were written to, or ``None`` when no plotted algorithm
            belongs to the grid - the bars then stay ungrouped, or keep the plot's own
            x-axis, rather than every one of them collapsing into a single group.
        """
        _ = benchmark_results

        kept = [row for row in rows if str(row.get("algorithm", "")) in self.labels]

        if not kept:
            logger.warning("No plotted algorithm belongs to the grid axis %r", self.title)
            return None

        # Only the grid's own algorithms, as `ParameterDimension` also does: a grid axis
        # is a statement about the variants of one algorithm, and a classical baseline in
        # the same benchmark has no value on it. Keeping the others would pool every one
        # of them into a single group and put the mean of unrelated runs on the axis.
        rows[:] = kept

        for row in rows:
            row[self.title] = self.labels[str(row["algorithm"])]

        return self.title


class MetricDimension(BaseModel):
    """What a plot measures: the number on the y-axis and what to call it.

    The counterpart of the dimensions above - they say what the data is organised by, this
    says what is being read off it. One number needs three things said about it: where it
    comes from, what column holds it, and what the axis is called; naming the attribute
    settles all three, since the column may as well be the attribute's own name:

    .. code-block:: python

        RuntimePlot(y=MetricDimension("runtime_seconds", "Runtime (s)"))

    Attributes
    ----------
    attribute : str
        Attribute read off the metric result, e.g. ``"runtime_seconds"`` - or off a
        feature result, for the plots that chart a property rather than a measurement. It
        doubles as the column the value is plotted from.
    label : str | None
        What the y-axis is called, by default the attribute's own name.
    scale : float
        Factor the value is read in, by default ``1.0`` - the unit the metric reports.
        `PERCENT` is what every built-in ratio uses, so a share of ``0.5`` reaches the
        axis as ``50``; the limits, the reference and the baseline are then in percent
        as well, since they are values on that same axis. An annotated percent axis
        wants ``Annotation(format="{:.1f}%")`` to match.
    limits : tuple[float, float] | None
        Lower and upper limit of the axis, by default the data range.
    reference : float | None
        Value of a dashed line across the plot, e.g. the optimum a ratio aims at.
    reference_label : str | None
        Legend label of that line. Without one it stays out of the legend.
    baseline : float | None
        Height of a solid, unlabelled line marking where the bars start. Unlike
        *reference* it says where zero is, it does not name a target.
    """

    model_config = ConfigDict(extra="forbid")

    attribute: str
    label: str | None = None
    scale: float = 1.0
    limits: tuple[float, float] | None = None
    reference: float | None = None
    reference_label: str | None = None
    baseline: float | None = None

    #: Result classes already reported as not carrying :attr:`attribute`.
    _warned_absent: set[str] = PrivateAttr(default_factory=set)

    def __init__(self, attribute: str | None = None, label: str | None = None, /, **data: Any) -> None:
        """Take the attribute and its title positionally, which is all there is to say.

        Parameters
        ----------
        attribute : str | None, optional
            Attribute read off the result.
        label : str | None, optional
            What the y-axis is called.
        **data : Any
            The remaining fields.
        """
        if attribute is not None:
            data["attribute"] = attribute
        if label is not None:
            data["label"] = label
        super().__init__(**data)

    @property
    def column(self) -> str:
        """Return the column the value is plotted from."""
        return self.attribute

    @property
    def title(self) -> str:
        """Return what the y-axis is called."""
        return self.label or self.attribute

    def of(self, result: Any) -> float:  # noqa: ANN401
        """Return the number *result* contributes, or ``nan`` where it has none.

        A metric reports nothing in more than one way: an attribute it never filled, or
        one that came back from the database as ``None`` because the value was an infinity
        and JSON has no word for that. Neither is a number, and neither is a reason to
        stop drawing - what becomes of a value a plot cannot draw is `Missing`, which
        reads a ``nan`` as exactly that.

        A result that does not carry the attribute at all is missing too, but it is also
        the one case that is usually a misspelling rather than a gap in the data. It says
        so in the log once, naming the result it looked at - otherwise a typo would reach
        the user as a figure complaining that every value of it is missing.

        Parameters
        ----------
        result : Any
            A metric or feature result.

        Returns
        -------
        float
            The value plotted for it, in the scale the axis is read in, or ``nan`` when
            the result carries none.
        """
        if not hasattr(result, self.attribute):
            # Asked before reading rather than reading with a default: a result that
            # reports nothing says so with a ``None``, and the two are not the same answer.
            self._warn_absent(type(result).__name__)
            return float("nan")

        value = getattr(result, self.attribute)
        return float("nan") if value is None else float(value) * self.scale

    def _warn_absent(self, result_type: str) -> None:
        """Say once that *result_type* has no attribute of this name.

        Parameters
        ----------
        result_type : str
            Name of the result class the attribute was looked for on.
        """
        if result_type in self._warned_absent:
            # One line per result class, not one per model and algorithm: every row of the
            # plot hits this, and they would all say the same thing.
            return

        self._warned_absent.add(result_type)
        logger.warning(
            "%s has no attribute '%s', so every value of it is missing. Check the name the "
            "dimension was given against the attributes the metric result carries.",
            result_type,
            self.attribute,
        )


#: The groupings a bar plot takes, told apart by their ``kind`` so that one survives being
#: stored with the benchmark and read back.
type Dimension = Annotated[
    ModelDimension | AlgorithmDimension | FeatureDimension | ParameterDimension | GridDimension,
    Field(discriminator="kind"),
]
