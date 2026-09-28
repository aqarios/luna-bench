"""What a solver reported about a run, and what reading it means when it reported nothing.

A run either carries metadata or it does not, and the difference matters to a metric: a key
that is missing from metadata the solver did send is a different problem from a solver that
sent none at all. An empty mapping cannot tell those apart, so this container keeps the
distinction and raises ``MetadataNotAvailableError`` on the second one.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict

from luna_bench.errors.components.algorithms.metadata_not_available_error import MetadataNotAvailableError


class SolveMetadata(BaseModel):
    """The metadata of one algorithm run.

    Attributes
    ----------
    data : dict[str, Any] | None
        What the algorithm reported, or ``None`` when it reported nothing. Read it through
        the accessors rather than directly, so an absent mapping raises instead of silently
        behaving like an empty one.

    Examples
    --------
    >>> metadata = SolveMetadata(data={"device": "qpu-7", "shots": 4096})
    >>> metadata["shots"]
    4096
    >>> metadata.get("queue_time_s", 0.0)
    0.0
    >>> SolveMetadata().available
    False
    """

    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any] | None = None

    @property
    def available(self) -> bool:
        """Whether the run reported any metadata at all."""
        return self.data is not None

    def as_dict(self) -> dict[str, Any]:
        """Return everything the run reported.

        Returns
        -------
        dict[str, Any]
            The full mapping.

        Raises
        ------
        MetadataNotAvailableError
            If the run reported no metadata.
        """
        if self.data is None:
            raise MetadataNotAvailableError
        return self.data

    def get(self, key: str, default: Any = None) -> Any:  # noqa: ANN401 # Metadata values are whatever the solver put there.
        """Return one value, or *default* if the run did not report that key.

        Parameters
        ----------
        key : str
            The key to read.
        default : Any, optional
            What to return when the key is absent.

        Returns
        -------
        Any
            The value, or *default*.

        Raises
        ------
        MetadataNotAvailableError
            If the run reported no metadata. A solver that reported nothing is not the same
            as one that reported everything but this key, so it is not answered with
            *default*.
        """
        return self.as_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401 # Metadata values are whatever the solver put there.
        """Return one value.

        Parameters
        ----------
        key : str
            The key to read.

        Returns
        -------
        Any
            The value.

        Raises
        ------
        MetadataNotAvailableError
            If the run reported no metadata.
        KeyError
            If the run reported metadata, but not this key.
        """
        return self.as_dict()[key]

    def __contains__(self, key: str) -> bool:
        """Whether the run reported *key*, answering ``False`` when it reported nothing."""
        return self.data is not None and key in self.data

    @classmethod
    def of(cls, data: Mapping[str, Any] | None) -> SolveMetadata:
        """Wrap what a run reported.

        Parameters
        ----------
        data : Mapping[str, Any] | None
            The reported mapping, or ``None``.

        Returns
        -------
        SolveMetadata
            The container.
        """
        return cls(data=dict(data) if data is not None else None)
