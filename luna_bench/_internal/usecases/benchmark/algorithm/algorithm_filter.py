from luna_quantum import Logging
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench._internal.usecases.benchmark.protocols import AlgorithmFilterUc
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError


class AlgorithmFilterUcImpl(AlgorithmFilterUc):
    _logger = Logging.get_logger(__name__)
    _logger.setLevel("DEBUG")

    def __call__(
        self, benchmark: BenchmarkUserModel, algorithm_type: AlgorithmType, algorithm: AlgorithmUserModel | None = None
    ) -> Result[list[AlgorithmUserModel], RunAlgorithmMissingError]:
        algorithms: list[AlgorithmUserModel]

        if algorithm is not None:
            if algorithm not in benchmark.algorithms:
                self._logger.debug(f"Algorithm {algorithm.name} is not part of the benchmark '{benchmark.name}'")
                return Failure(RunAlgorithmMissingError(algorithm.name, benchmark.name))
            self._logger.debug(f"Running single algorithm {[algorithm.name]} for benchmark '{benchmark.name}'")
            algorithms = [algorithm]
        else:
            self._logger.debug(
                f"Running all algorithms {[a.name for a in benchmark.algorithms]} for benchmark '{benchmark.name}"
            )
            algorithms = benchmark.algorithms

        match algorithm_type:
            case AlgorithmType.SYNC:
                algorithms = [a for a in algorithms if isinstance(a.algorithm, AlgorithmSync)]
            case AlgorithmType.ASYNC:
                algorithms = [a for a in algorithms if isinstance(a.algorithm, AlgorithmAsync)]
            case _:
                return Failure(ValueError(f"Unknown algorithm type: {algorithm_type}"))

        return Success(algorithms)
