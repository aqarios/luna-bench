from luna_bench.errors.base_error import BaseError


class ModelSetNotLoadedError(BaseError):
    """Raised when the modelset a benchmark references cannot be loaded."""

    def __init__(self, benchmark_name: str, modelset_name: str) -> None:
        self.benchmark_name = benchmark_name
        self.modelset_name = modelset_name
        super().__init__(
            f"Benchmark '{benchmark_name}' references modelset '{modelset_name}', but it "
            f"could not be loaded from the database, so models cannot be added or removed "
            f'through it. It may have been deleted: re-create it with `ModelSet.create("{modelset_name}")`, '
            f"or attach a different one with `benchmark.set_modelset(...)`."
        )
