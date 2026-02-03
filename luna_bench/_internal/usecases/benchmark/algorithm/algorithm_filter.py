from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmFilterUc
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync
from luna_bench.entities import AlgorithmEntity, BenchmarkEntity
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError


class AlgorithmFilterUcImpl(AlgorithmFilterUc):
    _logger = Logging.get_logger(__name__)

    def __call__(
        self, benchmark: BenchmarkEntity, algorithm_type: AlgorithmType, algorithm: AlgorithmEntity | None = None
    ) -> Result[list[AlgorithmEntity], RunAlgorithmMissingError]:
        algorithms: list[AlgorithmEntity]

        if algorithm is not None:
            if not any(a.name == algorithm.name for a in benchmark.algorithms):
                self._logger.debug(f"Algorithm {algorithm.name} is not part of the benchmark '{benchmark.name}'.")
                return Failure(RunAlgorithmMissingError(algorithm.name, benchmark.name))
            self._logger.debug(f"Selected a single algorithm {[algorithm.name]} for benchmark '{benchmark.name}'.")
            algorithms = [algorithm]
        else:
            self._logger.debug(
                f"Selected all algorithms {[a.name for a in benchmark.algorithms]} for benchmark '{benchmark.name}."
            )
            algorithms = benchmark.algorithms

        match algorithm_type:
            case AlgorithmType.SYNC:
                algorithms = [a for a in algorithms if isinstance(a.algorithm, BaseAlgorithmSync)]
            case AlgorithmType.ASYNC:
                algorithms = [a for a in algorithms if isinstance(a.algorithm, BaseAlgorithmAsync)]

        return Success(algorithms)
