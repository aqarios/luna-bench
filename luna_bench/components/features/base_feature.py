from typing import NamedTuple, TypeVar

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

T = TypeVar("T")
N = TypeVar("N", bound=NamedTuple)


class BaseFeatureResult[N, T](ArbitraryDataDomain):
    """Base class for feature calculating stats."""

    stats: dict[str, T]

    def get(self, enum_key: N) -> T:
        """Get stats by type and scope."""
        return self.stats[str(enum_key._asdict())]
