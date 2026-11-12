from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SkipValidation

from luna_bench.custom.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.custom.base_components.base_algorithm_sync import BaseAlgorithmSync
from luna_bench.custom.types import AlgorithmName, ModelName

from .algorithm_result_entity import AlgorithmResultEntity


class AlgorithmEntity(BaseModel):
    """Represents a fully configured algorithm."""

    name: AlgorithmName

    algorithm: SkipValidation[BaseAlgorithmSync | BaseAlgorithmAsync[Any]]

    #: How often this algorithm is run on every model of the benchmark. One unless the
    #: entry was added with ``repetitions``.
    repetitions: int = 1

    #: Key is the model name, value the runs on that model ordered by repetition. An
    #: algorithm added without ``repetitions`` has exactly one entry per list, so a
    #: single run is ``results[model][0]``.
    results: dict[ModelName, list[AlgorithmResultEntity]]

    def runs(self, model_name: ModelName) -> list[AlgorithmResultEntity]:
        """Return every run of this algorithm on one model, ordered by repetition.

        Parameters
        ----------
        model_name : ModelName
            The model the runs were made on.

        Returns
        -------
        list[AlgorithmResultEntity]
            The runs, empty if the algorithm has not run on that model at all.
        """
        return self.results.get(model_name, [])

    def run(self, model_name: ModelName, repetition: int = 0) -> AlgorithmResultEntity | None:
        """Return one run of this algorithm, by the repetition it belongs to.

        Addressed by repetition rather than by position, because a benchmark whose
        results were partly reset has the repetitions it still holds, not a dense range.

        Parameters
        ----------
        model_name : ModelName
            The model the run was made on.
        repetition : int, optional
            Which repetition to return, by default the first one.

        Returns
        -------
        AlgorithmResultEntity | None
            The run, or ``None`` if that repetition has no result.
        """
        return next((r for r in self.runs(model_name) if r.repetition == repetition), None)
