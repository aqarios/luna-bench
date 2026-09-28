"""Turning what an algorithm returned into the pair luna-bench stores.

An algorithm hands back a bare ``Solution``, or a ``(solution, metadata)`` pair when it knows
something about the run that the solution itself does not carry - the device it ran on, what
the provider queued it behind, how many shots it took. Both shapes arrive at the same two
places, the huey worker for synchronous algorithms and the retrieval use case for asynchronous
ones, so the widening lives here instead of in either of them.

Metadata is stored as bytes, next to the encoded solution and for the same reason: a provider
fills it with whatever it likes - datetimes, enums, nested numpy scalars - and pinning it to
what JSON can hold would quietly drop half of it.
"""

from collections.abc import Mapping
from typing import Any

import cloudpickle
from luna_model import Solution

from luna_bench.custom.types import SolveOutcome
from luna_bench.errors.decorators.invalid_return_type_error import InvalidReturnTypeError
from luna_bench.errors.metadata_decoding_error import MetadataDecodingError
from luna_bench.errors.metadata_encoding_error import MetadataEncodingError

#: How many elements a ``(solution, metadata)`` return has.
_OUTCOME_PAIR_LENGTH = 2


def split_solve_outcome(outcome: SolveOutcome, algorithm_name: str) -> tuple[Solution, dict[str, Any] | None]:
    """Split what an algorithm returned into its solution and its metadata.

    Parameters
    ----------
    outcome : SolveOutcome
        A ``Solution``, or a ``(solution, metadata)`` pair.
    algorithm_name : str
        Name of the algorithm, for the error message.

    Returns
    -------
    tuple[Solution, dict[str, Any] | None]
        The solution, and the metadata it came with - ``None`` when the algorithm returned
        the solution alone.

    Raises
    ------
    InvalidReturnTypeError
        If *outcome* is neither a ``Solution`` nor a pair of one and a mapping.
    """
    if isinstance(outcome, Solution):
        return outcome, None

    if not isinstance(outcome, tuple) or len(outcome) != _OUTCOME_PAIR_LENGTH:
        raise InvalidReturnTypeError(algorithm_name, Solution, type(outcome))

    solution, metadata = outcome

    if not isinstance(solution, Solution):
        raise InvalidReturnTypeError(algorithm_name, Solution, type(solution))

    if not isinstance(metadata, Mapping):
        raise InvalidReturnTypeError(algorithm_name, dict, type(metadata))

    return solution, dict(metadata)


def encode_metadata(metadata: Mapping[str, Any] | None, algorithm_name: str | None = None) -> bytes | None:
    """Serialize metadata for storage, keeping ``None`` as ``None``.

    Parameters
    ----------
    metadata : Mapping[str, Any] | None
        What the algorithm reported about the run.
    algorithm_name : str | None, optional
        Name of the algorithm, for the error message, where the caller knows it.

    Returns
    -------
    bytes | None
        The serialized mapping, or ``None`` if there was nothing to serialize.

    Raises
    ------
    MetadataEncodingError
        If the mapping holds something the serializer cannot handle.
    """
    if metadata is None:
        return None

    try:
        return bytes(cloudpickle.dumps(dict(metadata)))
    except Exception as e:
        raise MetadataEncodingError(e, algorithm_name) from e


def decode_metadata(raw: bytes | None) -> dict[str, Any] | None:
    """Deserialize stored metadata, keeping ``None`` as ``None``.

    Parameters
    ----------
    raw : bytes | None
        The stored bytes, or ``None`` if the run reported no metadata.

    Returns
    -------
    dict[str, Any] | None
        The metadata mapping, or ``None`` if there was nothing stored.

    Raises
    ------
    MetadataDecodingError
        If the bytes cannot be deserialized, or do not hold a mapping.
    """
    if raw is None:
        return None

    try:
        decoded: Any = cloudpickle.loads(bytes(raw))
    except Exception as e:
        raise MetadataDecodingError(e) from e

    if not isinstance(decoded, dict):
        msg = f"Expected a dict, got {type(decoded).__name__}."
        raise MetadataDecodingError(TypeError(msg))

    return decoded
