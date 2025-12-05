from typing import Any

from luna_bench._internal.background_tasks import HueyAlgorithmRunner
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRunAlgorithmAsyncUc


class BackgroundRunAlgorithmAsyncUcImpl(BackgroundRunAlgorithmAsyncUc):
    def __call__(self, algorithm: AlgorithmAsync[Any], model_id: int) -> str:
        return str(HueyAlgorithmRunner.run_async(algorithm, model_id).id)  # pragma: no cover
