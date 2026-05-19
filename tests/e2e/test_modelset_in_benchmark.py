from luna_bench import Benchmark, ModelSet
from tests.utils.luna_model import simple_model


class TestModelSetInBenchmark:
    def test_modelset_updated_in_benchmark(self) -> None:
        m1 = simple_model("m1")
        m2 = simple_model("m2")

        modelset: ModelSet = ModelSet.create("test_modelset")
        modelset.add(m1)

        benchmark: Benchmark = Benchmark.create("test_benchmark")
        benchmark.set_modelset(modelset)
        assert benchmark.modelset is not None

        assert len(benchmark.modelset.models) == 1

        modelset.add(m2)

        assert len(benchmark.modelset.models) == 2
