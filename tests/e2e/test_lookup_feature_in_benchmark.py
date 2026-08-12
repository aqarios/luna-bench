from enum import StrEnum

from luna_bench import Benchmark, ModelSet
from luna_bench.custom import BaseValueLookupFeature, feature
from luna_bench.features import OptSolFeature, OptSolFeatureResult
from tests.utils.luna_model import simple_model


class Difficulty(StrEnum):
    """Hand-assigned difficulty rating."""

    EASY = "easy"
    HARD = "hard"


@feature
class DifficultyLookupFeature(BaseValueLookupFeature[Difficulty]):
    """Maps each model to a hand-assigned difficulty."""


class TestLookupFeatureInBenchmark:
    """A populated lookup feature must survive being persisted and reconstructed."""

    def test_mapping_survives_the_benchmark_round_trip(self) -> None:
        easy = simple_model("easy_model")
        hard = simple_model("hard_model")

        modelset: ModelSet = ModelSet.create("lookup_modelset")
        modelset.add(easy)
        modelset.add(hard)

        difficulties = DifficultyLookupFeature()
        difficulties.add_models({easy: Difficulty.EASY, hard: Difficulty.HARD})

        benchmark: Benchmark = Benchmark.create("lookup_benchmark")
        benchmark.set_modelset(modelset)
        benchmark.add_feature(name="difficulty", feature=difficulties)

        reconstructed = Benchmark.load("lookup_benchmark").get_feature("difficulty").feature

        assert isinstance(reconstructed, DifficultyLookupFeature)
        assert reconstructed.mapping == difficulties.mapping
        assert reconstructed.run(easy).value == Difficulty.EASY
        assert reconstructed.run(hard).value == Difficulty.HARD

    def test_the_lookup_key_matches_the_hash_the_modelset_stores(self) -> None:
        """The mapping keys are exactly the hashes luna-bench already persists per model."""
        easy = simple_model("easy_model")
        hard = simple_model("hard_model")

        modelset: ModelSet = ModelSet.create("coverage_modelset")
        modelset.add(easy)
        modelset.add(hard)

        difficulties = DifficultyLookupFeature()
        difficulties.add_model(easy, Difficulty.EASY)

        stored_hashes = {m.name: m.hash for m in modelset.models}
        assert stored_hashes == {"easy_model": hash(easy), "hard_model": hash(hard)}

        assert difficulties.covers(easy) is True
        assert difficulties.covers(hard) is False


class TestPreComputedOptimaInBenchmark:
    """The precomputed optima have to reach the run, without any custom encoding."""

    def test_precomputed_optima_survive_the_benchmark_round_trip(self) -> None:
        known = simple_model("known_model")
        unknown = simple_model("unknown_model")

        modelset: ModelSet = ModelSet.create("precomp_modelset")
        modelset.add(known)
        modelset.add(unknown)

        optima = OptSolFeature()
        optima.add_model(known, OptSolFeatureResult(global_best_sol=42.0, pre_terminated=True))

        benchmark: Benchmark = Benchmark.create("precomp_benchmark")
        benchmark.set_modelset(modelset)
        benchmark.add_feature(name="optima", feature=optima)

        reconstructed = Benchmark.load("precomp_benchmark").get_feature("optima").feature

        assert isinstance(reconstructed, OptSolFeature)
        assert reconstructed.mapping == optima.mapping

        result = reconstructed.run(known)
        assert result.global_best_sol == 42.0
        assert result.pre_terminated is True
        assert result.runtime == 0.0

        assert reconstructed.covers(known) is True
        assert reconstructed.covers(unknown) is False
