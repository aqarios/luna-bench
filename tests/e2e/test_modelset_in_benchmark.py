from pathlib import Path

import pytest

from luna_bench import Benchmark, ModelSet
from luna_bench.errors.modelset_not_loaded_error import ModelSetNotLoadedError
from tests.utils.luna_model import simple_model, write_model_file


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

    def test_add_model_creates_modelset_named_after_benchmark(self) -> None:
        m1 = simple_model("m1")

        benchmark: Benchmark = Benchmark.create("auto_modelset_benchmark")
        benchmark.add_model(m1)

        assert benchmark.modelset is not None
        assert benchmark.modelset.name == "auto_modelset_benchmark"
        assert [m.name for m in benchmark.modelset.models] == ["m1"]

        # The models really are persisted under that modelset name.
        persisted = ModelSet.load("auto_modelset_benchmark")
        assert [m.name for m in persisted.models] == ["m1"]

    def test_add_model_accepts_iterable_and_remove_model_takes_them_back_out(self) -> None:
        m1 = simple_model("m1")
        m2 = simple_model("m2")

        benchmark: Benchmark = Benchmark.create("iterable_models_benchmark")
        benchmark.add_model([m1, m2])

        assert benchmark.modelset is not None
        assert {m.name for m in benchmark.modelset.models} == {"m1", "m2"}

        benchmark.remove_model([m1, m2])

        assert benchmark.modelset.models == []
        assert ModelSet.load("iterable_models_benchmark").models == []

    def test_loaded_benchmark_can_add_models_directly(self) -> None:
        m1 = simple_model("m1")
        m2 = simple_model("m2")

        modelset: ModelSet = ModelSet.create("loaded_bench_models")
        modelset.add(m1)

        benchmark: Benchmark = Benchmark.create("loaded_bench")
        benchmark.set_modelset(modelset)

        # A benchmark read back from the database acquires a live handle on its
        # modelset, so no set_modelset call is needed first.
        loaded: Benchmark = Benchmark.load("loaded_bench")
        assert isinstance(loaded.modelset, ModelSet)

        loaded.add_model(m2)

        assert {m.name for m in loaded.modelset.models} == {"m1", "m2"}
        assert {m.name for m in ModelSet.load("loaded_bench_models").models} == {"m1", "m2"}

    def test_opened_benchmark_can_add_models_directly(self) -> None:
        m1 = simple_model("m1")

        Benchmark.create("opened_bench").add_model(m1)

        reopened: Benchmark = Benchmark.open("opened_bench")
        reopened.add_model(simple_model("m2"))

        assert reopened.modelset is not None
        assert {m.name for m in reopened.modelset.models} == {"m1", "m2"}

    def test_rerunning_the_same_script_neither_raises_nor_duplicates(self) -> None:
        def script() -> Benchmark:
            benchmark: Benchmark = Benchmark.open("rerun_bench")
            benchmark.add_model([simple_model("m1"), simple_model("m2")])
            return benchmark

        script()
        second_run = script()

        assert second_run.modelset is not None
        assert sorted(m.name for m in second_run.modelset.models) == ["m1", "m2"]

    def test_add_model_from_a_single_file(self, tmp_path: Path) -> None:
        path = write_model_file(tmp_path, "single")

        benchmark: Benchmark = Benchmark.create("single_file_bench")
        benchmark.add_model(path)

        assert benchmark.modelset is not None
        assert [m.name for m in benchmark.modelset.models] == ["single"]

    def test_add_model_from_a_directory_adds_every_model_file(self, tmp_path: Path) -> None:
        write_model_file(tmp_path, "gamma")
        write_model_file(tmp_path, "alpha")
        write_model_file(tmp_path, "beta", suffix=".lp")
        (tmp_path / "README.txt").write_text("not a model")

        benchmark: Benchmark = Benchmark.create("model_folder_bench")
        benchmark.add_model(tmp_path)

        assert benchmark.modelset is not None
        assert sorted(m.name for m in benchmark.modelset.models) == ["alpha", "beta", "gamma"]

    def test_rerunning_a_directory_add_does_not_duplicate(self, tmp_path: Path) -> None:
        write_model_file(tmp_path, "alpha")
        write_model_file(tmp_path, "beta")

        Benchmark.open("rerun_folder_bench").add_model(tmp_path)
        second_run: Benchmark = Benchmark.open("rerun_folder_bench")
        second_run.add_model(tmp_path)

        assert second_run.modelset is not None
        assert sorted(m.name for m in second_run.modelset.models) == ["alpha", "beta"]

    def test_a_model_added_from_a_file_can_be_removed_by_the_same_path(self, tmp_path: Path) -> None:
        path = write_model_file(tmp_path, "removable")

        benchmark: Benchmark = Benchmark.create("remove_by_path_bench")
        benchmark.add_model(path)
        assert benchmark.modelset is not None
        assert [m.name for m in benchmark.modelset.models] == ["removable"]

        benchmark.remove_model(path)

        assert benchmark.modelset.models == []

    def test_add_model_raises_when_the_referenced_modelset_was_deleted(self) -> None:
        modelset: ModelSet = ModelSet.create("vanishing_models")
        modelset.add(simple_model("m1"))

        benchmark: Benchmark = Benchmark.create("vanished_modelset_bench")
        benchmark.set_modelset(modelset)
        modelset.delete()

        loaded: Benchmark = Benchmark.load("vanished_modelset_bench")

        if loaded.modelset is None:
            pytest.skip("deleting a modelset detaches it from the benchmark")

        with pytest.raises(ModelSetNotLoadedError):
            loaded.add_model(simple_model("m2"))

    def test_add_model_still_works_after_reset(self) -> None:
        m1 = simple_model("m1")
        m2 = simple_model("m2")

        benchmark: Benchmark = Benchmark.create("reset_modelset_benchmark")
        benchmark.add_model(m1)

        benchmark.reset(mode="All")

        benchmark.add_model(m2)

        assert benchmark.modelset is not None
        assert {m.name for m in benchmark.modelset.models} == {"m1", "m2"}

    def test_remove_model_not_in_modelset_raises_runtime_error(self) -> None:
        m1 = simple_model("m1")
        m2 = simple_model("m2")

        benchmark: Benchmark = Benchmark.create("remove_absent_model_benchmark")
        benchmark.add_model(m1)

        with pytest.raises(RuntimeError):
            benchmark.remove_model(m2)
