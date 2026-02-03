from typing import NamedTuple, TypeVar

from pydantic import Field

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

T = TypeVar("T")
N = TypeVar("N", bound=NamedTuple)


class BaseFeatureResult[N, T](ArbitraryDataDomain):
    """
    Base class for feature results that store stats keyed by a NamedTuple.

    Subclasses are parameterized with a NamedTuple key type ``N`` and a stats
    value type ``T``. Stats are stored internally as ``dict[str, T]`` where the
    string key is the ``str(enum_key._asdict())`` representation.

    Example
    -------
    .. code-block:: python

        from typing import NamedTuple

        from pydantic import BaseModel

        from luna_bench.components.features.base_feature import BaseFeatureResult


        class MyKey(NamedTuple):
            name: str

        class MyStats(BaseModel):
            value: float

        class MyResult(BaseFeatureResult[MyKey, MyStats]):
            pass

        result = MyResult()
        result.add(enum_key=MyKey(name="a"), value=MyStats(value=1.0))
        stats = result.get(enum_key=MyKey(name="a"))
        stats.value  # 1.0
    """

    stats: dict[str, T] = Field(default_factory=dict)

    def get(self, enum_key: N) -> T:
        """Get stats by type and scope."""
        return self.stats[str(enum_key._asdict())]  # type: ignore[attr-defined]

    def add(self, enum_key: N, value: T) -> None:
        """Add stats by type and scope."""
        self.stats[str(enum_key._asdict())] = value  # type: ignore[attr-defined]
