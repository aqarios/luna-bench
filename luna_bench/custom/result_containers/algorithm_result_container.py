from __future__ import annotations

from typing import Any

from luna_model import Solution
from pydantic import BaseModel, ConfigDict, SkipValidation

from luna_bench.custom.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.custom.base_components.base_algorithm_sync import BaseAlgorithmSync


class AlgorithmResultContainer(BaseModel):
    """Container for the outcome of a single algorithm run.

    Bundles the (optional) solution, run metadata, and the configured
    algorithm instance that produced it, so consumers such as exporters can
    access results without depending on the entity layer.

    One container is a single run: an algorithm added with ``repetitions`` has one per
    repetition for the same (model, algorithm) pair, told apart by :attr:`repetition`.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    solution: Solution | None = None
    metadata: dict[str, Any] | None = None
    algorithm: SkipValidation[BaseAlgorithmSync | BaseAlgorithmAsync[Any]]

    #: Which run of the algorithm on this model this is, counted from 0.
    repetition: int = 0
