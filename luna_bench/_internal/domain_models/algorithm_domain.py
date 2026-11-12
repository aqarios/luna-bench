from __future__ import annotations

from .algorithm_result_domain import AlgorithmResultDomain
from .algorithm_type_enum import AlgorithmType
from .base_domain import BaseDomain
from .registered_data_domain import RegisteredDataDomain


class AlgorithmDomain(BaseDomain):
    name: str

    algorithm_type: AlgorithmType
    repetitions: int = 1
    #: Key is the model name, value the runs on that model ordered by repetition.
    results: dict[str, list[AlgorithmResultDomain]]

    config_data: RegisteredDataDomain
