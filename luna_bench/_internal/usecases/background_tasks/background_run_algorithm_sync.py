from luna_bench._internal.background_tasks import HueyAlgorithmRunner
from luna_bench._internal.interfaces import AlgorithmSync
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRunAlgorithmSyncUc


class BackgroundRunAlgorithmSyncUcImpl(BackgroundRunAlgorithmSyncUc):
    def __call__(self, algorithm: AlgorithmSync, model_id: int) -> str:
        return str(HueyAlgorithmRunner.run_sync(algorithm, model_id).id)  # pragma: no cover
