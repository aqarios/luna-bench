"""Base classes for features that serve a value looked up per model rather than computed from it.

Some model properties cannot be derived from the model itself - a problem category
("graph", "scheduling"), a source dataset, a difficulty rating, a known optimum. They
are assigned externally and simply need to reach metrics and plots alongside computed
features.

`BaseModelLookupFeature` is the generic base for that: a mapping from ``hash(model)`` to
a value of the subclass' choosing. Subclasses fix the value type (and, if needed, the
result type) via type parameters, so a concrete lookup feature is usually a class body
with nothing in it.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, ClassVar, cast
from typing import TypeVar as _TypeVar

from luna_model import Model
from pydantic import Field

from luna_bench.custom.base_results.feature_result import FeatureResult
from luna_bench.custom.base_results.lookup_feature_result import LookupFeatureResult
from luna_bench.errors.model_lookup_miss_error import ModelLookupMissError

from .base_feature import BaseFeature


class BaseModelLookupFeature[TValue, TFeatureResult: FeatureResult](BaseFeature[TFeatureResult], ABC):
    """
    Base class for features whose value is assigned per model instead of computed from it.

    The mapping is keyed by ``hash(model)``, the same structural hash luna-bench already
    stores as `ModelMetadataEntity.hash`. It is stable across the ``encode()``/``decode()``
    round-trip a benchmark performs before running features, and it covers the model's name
    as well as its contents, so models that differ in either get distinct keys.

    A miss raises `ModelLookupMissError`. Subclasses that can derive the value themselves
    override `on_miss`.

    Attributes
    ----------
    mapping : dict[int, TValue]
        ``hash(model)`` to assigned value. Populate it with `add_model` rather than by
        hand, so keys can never drift from their models.

    Notes
    -----
    Populate the feature *before* handing it to ``Benchmark.add_feature()``. The benchmark
    serializes the feature's configuration at that point and reconstructs it from the
    database when the run happens, so entries added to the in-memory object afterwards
    never reach the run.
    """

    mapping: dict[int, TValue] = Field(default_factory=dict)

    def add_model(self, model: Model, value: TValue) -> None:
        """
        Register ``value`` for ``model``, replacing any existing entry.

        Parameters
        ----------
        model : Model
            The model to assign a value to.
        value : TValue
            The value to serve whenever this model is seen.
        """
        self.mapping[hash(model)] = value

    def add_models(self, entries: Mapping[Model, TValue] | Iterable[tuple[Model, TValue]]) -> None:
        """
        Register several models at once.

        Parameters
        ----------
        entries : Mapping[Model, TValue] | Iterable[tuple[Model, TValue]]
            Model/value pairs, either as a mapping or as an iterable of tuples.
        """
        pairs: Iterable[tuple[Model, TValue]] = (
            cast("Mapping[Model, TValue]", entries).items() if isinstance(entries, Mapping) else entries
        )
        for model, value in pairs:
            self.add_model(model, value)

    def covers(self, model: Model) -> bool:
        """
        Return whether ``model`` has an entry, without running the feature.

        Useful for validating a mapping against a modelset up front instead of discovering
        gaps as failed feature results mid-run.

        Parameters
        ----------
        model : Model
            The model to check.

        Returns
        -------
        bool
            True if the model has an entry in the mapping.
        """
        return hash(model) in self.mapping

    def run(self, model: Model) -> TFeatureResult:
        """
        Return the registered value for ``model``.

        Parameters
        ----------
        model : Model
            The model to look up.

        Returns
        -------
        TFeatureResult
            The registered value, wrapped by `to_result`.

        Raises
        ------
        ModelLookupMissError
            If the model has no entry and `on_miss` is not overridden.
        """
        key = hash(model)
        if key not in self.mapping:
            return self.on_miss(model)
        return self.to_result(self.mapping[key], model)

    @abstractmethod
    def to_result(self, value: TValue, model: Model) -> TFeatureResult:
        """
        Wrap a looked-up ``value`` in this feature's result type.

        Parameters
        ----------
        value : TValue
            The value registered for ``model``.
        model : Model
            The model the value was looked up for.

        Returns
        -------
        TFeatureResult
            The feature result carrying the value.
        """

    def on_miss(self, model: Model) -> TFeatureResult:
        """
        Handle a model with no entry. Raises by default; override to compute one.

        Parameters
        ----------
        model : Model
            The model that has no entry in the mapping.

        Returns
        -------
        TFeatureResult
            Never returns in the base implementation.

        Raises
        ------
        ModelLookupMissError
            Always, unless a subclass overrides this method.
        """
        raise ModelLookupMissError(model_name=model.name, model_key=hash(model), feature_name=type(self).__name__)


class BaseValueLookupFeature[TValue](BaseModelLookupFeature[TValue, LookupFeatureResult[TValue]], ABC):
    """
    A `BaseModelLookupFeature` that reports its value as-is.

    This is the base to reach for. A concrete feature only names its value type; the result
    type is derived from it automatically, so a ``BaseValueLookupFeature[ProblemCategory]``
    subclass yields ``LookupFeatureResult[ProblemCategory]`` and validates against that enum
    on both input and output.

    Attributes
    ----------
    result_cls : ClassVar[Any]
        The parametrized `LookupFeatureResult` this subclass produces. Bound automatically
        when the subclass is created.

    Examples
    --------
    >>> @feature
    ... class DifficultyFeature(BaseValueLookupFeature[int]):
    ...     '''Hand-assigned difficulty rating per model.'''
    >>> f = DifficultyFeature()
    >>> f.add_model(model, 3)
    >>> f.run(model).value
    3
    """

    result_cls: ClassVar[Any] = LookupFeatureResult

    def __init__(self, **data: Any) -> None:
        """
        Reject instantiation of the unparametrized base class.

        Unlike `BaseModelLookupFeature`, this class has no abstract methods left, so ABC
        alone would not stop it from being instantiated - but without a concrete value type
        its `result_cls` is the unparametrized `LookupFeatureResult`, which validates
        nothing.

        Parameters
        ----------
        **data : Any
            Field values forwarded to pydantic.

        Raises
        ------
        TypeError
            If instantiated directly instead of through a subclass.
        """
        if type(self) is BaseValueLookupFeature:
            msg = (
                "BaseValueLookupFeature is abstract. Subclass it with a concrete value type, "
                "e.g. 'class DifficultyFeature(BaseValueLookupFeature[int]): ...'."
            )
            raise TypeError(msg)
        super().__init__(**data)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Bind ``result_cls`` to ``LookupFeatureResult[<concrete value type>]``.

        Walks the MRO for the nearest base parametrized with a concrete type - pydantic
        records each parametrization in ``__pydantic_generic_metadata__`` - so subclasses
        get a validating, self-describing result type for free.

        Without this, `to_result` would build ``LookupFeatureResult[TValue]`` with the
        unbound type variable, giving every subclass the same unvalidated result class.
        `__pydantic_init_subclass__` is used rather than ``__init_subclass__`` because it
        runs after pydantic has finished building the class; ``__init_subclass__`` fires
        before the parametrization metadata is available.

        Parameters
        ----------
        **kwargs : Any
            Class keyword arguments forwarded to pydantic.
        """
        super().__pydantic_init_subclass__(**kwargs)
        for base in cls.__mro__:
            args = getattr(base, "__pydantic_generic_metadata__", {}).get("args", ())
            if len(args) == 1 and not isinstance(args[0], _TypeVar):
                # The parametrization is only known at runtime, so the subscript cannot be typed.
                cls.result_cls = LookupFeatureResult[args[0]]  # type: ignore[valid-type]
                return

    def to_result(self, value: TValue, model: Model) -> LookupFeatureResult[TValue]:  # noqa: ARG002
        """
        Wrap ``value`` in this subclass' parametrized result type.

        Parameters
        ----------
        value : TValue
            The value registered for ``model``.
        model : Model
            The model the value was looked up for. Unused.

        Returns
        -------
        LookupFeatureResult[TValue]
            The value wrapped in this subclass' result type.
        """
        result: LookupFeatureResult[TValue] = type(self).result_cls(value=value)
        return result
