from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar

from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.components.helper.var_scope import VarScope

# Type variables for the dimension enums
T = TypeVar("T", bound=Enum)  # Primary type dimension (CoefType, NormType, NodeType, etc.)
U = TypeVar("U", bound=Enum)  # Secondary dimension (VarScope or other)

# Type variable for the stats container (CoefStats, ObjCoefStats, etc.)
S = TypeVar("S", bound=BaseModel)


class BaseStatsResult1D[T: Enum, S: BaseModel](ABC, ArbitraryDataDomain):
    """
    Abstract base class for feature results using a one-dimensional stats structure.

    Provides common access patterns for stats organized by a single type dimension (T).

    Access patterns:
        - result.get(type) -> S
        - result.get_mean(type) -> float
        - result.all_stats() -> Dict[T, S]

    Attributes
    ----------
    stats : Dict[str, S]
        Dictionary mapping type keys to stats objects.
    """

    stats: dict[str, S]

    @staticmethod
    @abstractmethod
    def _type_enum() -> type[T]:
        """Return the enum class used for the type dimension."""
        ...

    @staticmethod
    def make_key(type_value: Enum) -> str:
        """Create a string key from type."""
        return type_value.value

    def get(self, type_value: T) -> S:
        """
        Get stats by type.

        Parameters
        ----------
        type_value : T
            The type dimension value.

        Returns
        -------
        S
            The statistics for the specified type.
        """
        return self.stats[self.make_key(type_value)]

    def get_mean(self, type_value: T) -> float:
        """Direct access to mean value."""
        return self.get(type_value).mean

    def all_stats(self) -> dict[T, S]:
        """Get all stats as a dict keyed by type enum."""
        type_enum = self._type_enum()
        return {type_enum(k): v for k, v in self.stats.items()}


class BaseStatsResult2D[T: Enum, U: Enum, S: BaseModel](ABC, ArbitraryDataDomain):
    """
    Abstract base class for feature results using a two-dimensional stats structure.

    Provides common access patterns for stats organized by a primary type dimension (T)
    and a secondary dimension (U), typically VarScope.

    Access patterns:
        - result.get(type, scope) -> S
        - result.get_mean(type, scope) -> float
        - result.by_type(type) -> Dict[U, S]
        - result.by_scope(scope) -> Dict[T, S]

    Attributes
    ----------
    stats : Dict[str, S]
        Dictionary mapping "{type}_{scope}" keys to stats objects.
    """

    stats: dict[str, S]

    @staticmethod
    @abstractmethod
    def _type_enum() -> type[T]:
        """Return the enum class used for the primary type dimension."""
        ...

    @staticmethod
    @abstractmethod
    def _scope_enum() -> type[U]:
        """Return the enum class used for the secondary scope dimension."""
        ...

    @staticmethod
    def make_key(type_value: Enum, scope_value: Enum) -> str:
        """Create a string key from type and scope."""
        return f"{type_value.value}_{scope_value.value}"

    def get(self, type_value: T, scope_value: U) -> S:
        """
        Get stats by type and scope.

        Parameters
        ----------
        type_value : T
            The primary type dimension value.
        scope_value : U
            The secondary scope dimension value.

        Returns
        -------
        S
            The statistics for the specified type and scope.
        """
        return self.stats[self.make_key(type_value, scope_value)]

    def get_mean(self, type_value: T, scope_value: U) -> float:
        """Direct access to mean value."""
        return self.get(type_value, scope_value).mean

    def by_type(self, type_value: T) -> dict[U, S]:
        """Get all stats for a given type."""
        scope_enum = self._scope_enum()
        return {scope_enum(k.split("_", 1)[1]): v for k, v in self.stats.items() if k.startswith(type_value.value)}

    def by_scope(self, scope_value: U) -> dict[T, S]:
        """Get all stats for a given scope."""
        type_enum = self._type_enum()
        return {type_enum(k.rsplit("_", 1)[0]): v for k, v in self.stats.items() if k.endswith(scope_value.value)}


# Convenience alias for the common case where secondary dimension is VarScope
class BaseStatsResultWithVarScope[T: Enum, S: BaseModel](BaseStatsResult2D[T, VarScope, S], ABC):
    """
    Convenience base class for two-dimensional stats with VarScope as the secondary dimension.

    This is the most common pattern in LunaBench features.
    """

    @staticmethod
    def _scope_enum() -> type[VarScope]:
        """Return VarScope as the secondary dimension."""
        return VarScope
