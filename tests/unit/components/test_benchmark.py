import json
import logging
from collections.abc import Generator
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from returns.result import Failure, Success

from luna_bench import Benchmark, ModelSet
from luna_bench._internal.wrappers import LunaAlgorithmWrapper
from luna_bench.custom import BenchmarkResultContainer
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    FeatureEntity,
    JobStatus,
    MetricEntity,
    ModelMetadataEntity,
    ModelSetEntity,
    PlotEntity,
)
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.modelset_not_loaded_error import ModelSetNotLoadedError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.exporters import DataFrameExporter
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric, MockPlot
from tests.unit.fixtures.mock_entities import make_algo_entity, make_feature_entity, make_metric_entity
from tests.utils.luna_model import simple_model


class TestBenchmark:
    @pytest.fixture(autouse=True)
    def mocked_usecases(self) -> Generator[dict[str, MagicMock]]:
        from luna_bench import _usecase_container

        mocks = {}
        # ExitStack allows us to manage a dynamic number of context managers (overrides)
        with ExitStack() as stack:
            for name, provider in _usecase_container.providers.items():
                if name.endswith("_uc"):  # Currently all our usecases are marked with "_uc" suffix
                    mock = MagicMock(name=name)
                    stack.enter_context(provider.override(mock))
                    mocks[name] = mock

            yield mocks

    @pytest.fixture()
    def empty_benchmark(self) -> Benchmark:
        return Benchmark.model_construct(
            **BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[]).model_dump()
        )

    def test_create_success(self, mocked_usecases: dict[str, MagicMock]) -> None:
        mock = mocked_usecases["benchmark_create_uc"]
        benchmark_entity = BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[])

        mock.return_value = Success(benchmark_entity)
        b = Benchmark.create(benchmark_entity.name)
        assert b.model_dump() == benchmark_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            RuntimeError("test error"),
            ValueError("test error"),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_create_failure(self, error: Exception, mocked_usecases: dict[str, MagicMock]) -> None:
        mock = mocked_usecases["benchmark_create_uc"]
        mock.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()
        with pytest.raises(type(error)) as exc_info:
            Benchmark.create("test")
        assert exc_info.value == error

    def test_load_success(self, mocked_usecases: dict[str, MagicMock]) -> None:
        mock = mocked_usecases["benchmark_load_uc"]
        benchmark_entity = BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[])
        mock.return_value = Success(benchmark_entity)

        assert Benchmark.load(benchmark_entity.name).model_dump() == benchmark_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_load_failure(self, error: Exception, mocked_usecases: dict[str, MagicMock]) -> None:
        mock = mocked_usecases["benchmark_load_uc"]

        mock.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            Benchmark.load("test")
        assert exc_info.value == error

    def test_load_all_success(self, mocked_usecases: dict[str, MagicMock]) -> None:
        mock = mocked_usecases["benchmark_load_all_uc"]
        benchmark_entity = BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[])
        mock.return_value = Success([benchmark_entity])

        benchmarks = Benchmark.load_all()
        assert len(benchmarks) == 1
        assert benchmarks[0].model_dump() == benchmark_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            UnknownIdError(registry="xd", registered_id="xd"),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_load_all_failure(self, error: Exception, mocked_usecases: dict[str, MagicMock]) -> None:
        mock = mocked_usecases["benchmark_load_all_uc"]

        mock.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            Benchmark.load_all()
        assert exc_info.value == error

    def test_add_feature_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_feature_uc"]
        feature_entity = FeatureEntity(name="feat", feature=MockFeature(), results={})
        mock_add.return_value = Success(feature_entity)

        res = empty_benchmark.add_feature("feat", MagicMock())
        assert res.model_dump() == feature_entity.model_dump()
        assert len(empty_benchmark.features) == 1
        assert empty_benchmark.features[0].model_dump() == feature_entity.model_dump()

    @pytest.mark.parametrize(
        "error", [DataNotExistError(), UnknownLunaBenchError(exception=RuntimeError("another error"))]
    )
    @pytest.mark.parametrize(
        ("uc_key", "method", "entity_name"),
        [
            ("benchmark_add_feature_uc", "add_feature", "feat"),
            ("benchmark_add_metric_uc", "add_metric", "met"),
            ("benchmark_add_algorithm_uc", "add_algorithm", "algo"),
            ("benchmark_add_plot_uc", "add_plot", "plot"),
        ],
    )
    def test_add_component_failure(
        self,
        uc_key: str,
        method: str,
        entity_name: str,
        error: Exception,
        mocked_usecases: dict[str, MagicMock],
        empty_benchmark: Benchmark,
    ) -> None:
        mocked_usecases[uc_key].return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            getattr(empty_benchmark, method)(entity_name, MagicMock())
        assert exc_info.value == error

    def test_add_algorithm_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_algorithm_uc"]
        algorithm_entity = AlgorithmEntity(name="algo", algorithm=MockAlgorithm(), results={})
        mock_add.return_value = Success(algorithm_entity)

        res = empty_benchmark.add_algorithm("algo", MagicMock())
        assert res.model_dump() == algorithm_entity.model_dump()
        assert len(empty_benchmark.algorithms) == 1
        assert empty_benchmark.algorithms[0].model_dump() == algorithm_entity.model_dump()

    def test_add_metric_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_metric_uc"]
        metric_entity = MetricEntity(name="met", metric=MockMetric(), results={})
        mock_add.return_value = Success(metric_entity)

        res = empty_benchmark.add_metric("met", MagicMock())
        assert res.model_dump() == metric_entity.model_dump()
        assert len(empty_benchmark.metrics) == 1
        assert empty_benchmark.metrics[0].model_dump() == metric_entity.model_dump()

    def test_add_plot_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_plot_uc"]
        plot_entity = PlotEntity(name="plot", plot=MockPlot())
        mock_add.return_value = Success(plot_entity)

        res = empty_benchmark.add_plot("plot", MagicMock())
        assert res.model_dump() == plot_entity.model_dump()
        assert len(empty_benchmark.plots) == 1
        assert empty_benchmark.plots[0].model_dump() == plot_entity.model_dump()

    def test_set_modelset_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_set = mocked_usecases["benchmark_set_modelset_uc"]
        mock_set.return_value = Success(None)

        modelset = MagicMock(spec=ModelSet)
        modelset.name = "test_modelset"
        empty_benchmark.set_modelset(modelset)
        assert empty_benchmark.modelset == modelset
        mock_set.assert_called_once_with(empty_benchmark.name, "test_modelset")

    def test_set_modelset_by_name_loads_it_first(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mocked_usecases["benchmark_set_modelset_uc"].return_value = Success(None)
        loaded = MagicMock(spec=ModelSet)
        loaded.name = "by_name"

        with patch.object(ModelSet, "load", return_value=loaded) as mock_load:
            empty_benchmark.set_modelset("by_name")

        mock_load.assert_called_once_with("by_name")
        assert empty_benchmark.modelset == loaded

    def test_reset_failure_raises(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        error = DataNotExistError()
        mocked_usecases["benchmark_reset_uc"].return_value = Failure(error)

        with pytest.raises(DataNotExistError) as exc_info:
            empty_benchmark.reset(mode="All")

        assert exc_info.value is error

    def test_reset_unwraps_an_unknown_error(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        inner = RuntimeError("boom")
        mocked_usecases["benchmark_reset_uc"].return_value = Failure(UnknownLunaBenchError(exception=inner))

        with pytest.raises(RuntimeError) as exc_info:
            empty_benchmark.reset(mode="All")

        assert exc_info.value is inner

    def test_add_algorithm_wraps_a_luna_quantum_algorithm(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        algo_entity = AlgorithmEntity(name="wrapped", algorithm=MockAlgorithm(), results={})
        mocked_usecases["benchmark_add_algorithm_uc"].return_value = Success(algo_entity)
        raw = MagicMock(spec=IAlgorithm)

        with patch.object(LunaAlgorithmWrapper, "wrap", return_value=MockAlgorithm()) as mock_wrap:
            empty_benchmark.add_algorithm(name="wrapped", algorithm=raw)

        mock_wrap.assert_called_once_with(raw)

    def test_remove_modelset_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        empty_benchmark.modelset = MagicMock(spec=ModelSet)
        mock_remove = mocked_usecases["benchmark_remove_modelset_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_modelset()
        assert empty_benchmark.modelset is None
        mock_remove.assert_called_once_with(empty_benchmark.name)

    def test_remove_modelset_not_set(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_remove = mocked_usecases["benchmark_remove_modelset_uc"]

        empty_benchmark.remove_modelset()
        mock_remove.assert_not_called()

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_set_modelset_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_set = mocked_usecases["benchmark_set_modelset_uc"]
        mock_set.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        modelset = MagicMock(spec=ModelSet)
        modelset.name = "test_modelset"
        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.set_modelset(modelset)
        assert exc_info.value == error

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_remove_modelset_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        empty_benchmark.modelset = MagicMock(spec=ModelSet)
        mock_remove = mocked_usecases["benchmark_remove_modelset_uc"]
        mock_remove.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.remove_modelset()
        assert exc_info.value == error

    def test_remove_feature_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        feature_entity = FeatureEntity(name="feat", feature=MockFeature(), results={})
        empty_benchmark.features.append(feature_entity)

        mock_remove = mocked_usecases["benchmark_remove_feature_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_feature("feat")
        assert len(empty_benchmark.features) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "feat")

    def test_remove_metric_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        metric_entity = MetricEntity(name="met", metric=MockMetric(), results={})
        empty_benchmark.metrics.append(metric_entity)

        mock_remove = mocked_usecases["benchmark_remove_metric_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_metric("met")
        assert len(empty_benchmark.metrics) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "met")

    def test_remove_algorithm_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        algorithm_entity = AlgorithmEntity(name="algo", algorithm=MockAlgorithm(), results={})
        empty_benchmark.algorithms.append(algorithm_entity)

        mock_remove = mocked_usecases["benchmark_remove_algorithm_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_algorithm("algo")
        assert len(empty_benchmark.algorithms) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "algo")

    def test_remove_plot_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        plot_entity = PlotEntity(name="plot", plot=MockPlot())
        empty_benchmark.plots.append(plot_entity)

        mock_remove = mocked_usecases["benchmark_remove_plot_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_plot("plot")
        assert len(empty_benchmark.plots) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "plot")

    @pytest.mark.parametrize(
        "error", [DataNotExistError(), UnknownLunaBenchError(exception=RuntimeError("another error"))]
    )
    @pytest.mark.parametrize(
        ("uc_key", "method", "entity_name"),
        [
            ("benchmark_remove_feature_uc", "remove_feature", "feat"),
            ("benchmark_remove_metric_uc", "remove_metric", "met"),
            ("benchmark_remove_algorithm_uc", "remove_algorithm", "algo"),
            ("benchmark_remove_plot_uc", "remove_plot", "plot"),
        ],
    )
    def test_remove_component_failure(
        self,
        uc_key: str,
        method: str,
        entity_name: str,
        error: Exception,
        mocked_usecases: dict[str, MagicMock],
        empty_benchmark: Benchmark,
    ) -> None:
        mocked_usecases[uc_key].return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            getattr(empty_benchmark, method)(entity_name)
        assert exc_info.value == error

    def test_run_features_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock = mocked_usecases["benchmark_run_feature_uc"]
        mock.return_value = Success(None)
        empty_benchmark.run_features()
        mock.assert_called_once_with(empty_benchmark)

    @pytest.mark.parametrize(
        "error",
        [
            RunFeatureMissingError(feature_name="feat", benchmark_name="test"),
            RunModelsetMissingError(benchmark_name="test"),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_run_features_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock = mocked_usecases["benchmark_run_feature_uc"]
        mock.return_value = Failure(error)
        with pytest.raises(RuntimeError) as exc_info:
            empty_benchmark.run_features()
        assert exc_info.value.args[0] == error

    def test_run_algorithms_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock = mocked_usecases["benchmark_run_algorithm_uc"]
        mock.return_value = Success(None)
        empty_benchmark.run_algorithms()
        mock.assert_called_once_with(empty_benchmark)

    @pytest.mark.parametrize(
        "error",
        [
            RunAlgorithmMissingError(algorithm_name="algo", benchmark_name="test"),
            RunModelsetMissingError(benchmark_name="test"),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_run_algorithms_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock = mocked_usecases["benchmark_run_algorithm_uc"]
        mock.return_value = Failure(error)
        with pytest.raises(RuntimeError) as exc_info:
            empty_benchmark.run_algorithms()
        assert exc_info.value.args[0] == error

    def test_run_metrics_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock = mocked_usecases["benchmark_run_metric_uc"]
        mock.return_value = Success(None)
        empty_benchmark.run_metrics()
        mock.assert_called_once_with(empty_benchmark)

    @pytest.mark.parametrize(
        "error",
        [
            RunMetricMissingError(metric_name="met", benchmark_name="test"),
            RunModelsetMissingError(benchmark_name="test"),
            RunFeatureMissingError(feature_name="feat", benchmark_name="test"),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_run_metrics_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock = mocked_usecases["benchmark_run_metric_uc"]
        mock.return_value = Failure(error)
        with pytest.raises(RuntimeError) as exc_info:
            empty_benchmark.run_metrics()
        assert exc_info.value.args[0] == error

    def test_run_plots_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock = mocked_usecases["benchmark_run_plots_uc"]
        mock.return_value = Success(None)
        empty_benchmark.run_plots()

        args, _ = mock.call_args
        assert args[0] == empty_benchmark

    def test_run_plots_failure(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        error = UnknownLunaBenchError(exception=RuntimeError("another error"))
        mock = mocked_usecases["benchmark_run_plots_uc"]
        mock.return_value = Failure(error)
        with pytest.raises(RuntimeError) as exc_info:
            empty_benchmark.run_plots()
        assert exc_info.value.args[0] == error

    def test_run_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mocked_usecases["benchmark_run_feature_uc"].return_value = Success(None)
        mocked_usecases["benchmark_run_algorithm_uc"].return_value = Success(None)
        mocked_usecases["benchmark_run_metric_uc"].return_value = Success(None)
        mocked_usecases["benchmark_run_plots_uc"].return_value = Success(None)

        empty_benchmark.run()

        mocked_usecases["benchmark_run_feature_uc"].assert_called_once_with(empty_benchmark)
        mocked_usecases["benchmark_run_algorithm_uc"].assert_called_once_with(empty_benchmark)
        mocked_usecases["benchmark_run_metric_uc"].assert_called_once_with(empty_benchmark)

        # for plots it's called with default mode
        args, _ = mocked_usecases["benchmark_run_plots_uc"].call_args
        assert args[0] == empty_benchmark

    def test_open_existing_benchmark(self, mocked_usecases: dict[str, MagicMock]) -> None:
        mock_load = mocked_usecases["benchmark_load_uc"]
        benchmark_entity = BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[])
        mock_load.return_value = Success(benchmark_entity)

        b = Benchmark.open("test")
        assert b.model_dump() == benchmark_entity.model_dump()

    def test_open_creates_when_not_found(self, mocked_usecases: dict[str, MagicMock]) -> None:
        benchmark_entity = BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[])
        mock_load = mocked_usecases["benchmark_load_uc"]
        mock_create = mocked_usecases["benchmark_create_uc"]
        mock_load.return_value = Failure(DataNotExistError())
        mock_create.return_value = Success(benchmark_entity)

        b = Benchmark.open("test")
        assert b.model_dump() == benchmark_entity.model_dump()
        mock_create.assert_called_once_with("test")

    @pytest.mark.parametrize(
        "error",
        [
            UnknownIdError(registry="xd", registered_id="xd"),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_open_failure(self, error: Exception, mocked_usecases: dict[str, MagicMock]) -> None:
        mock_load = mocked_usecases["benchmark_load_uc"]
        mock_load.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            Benchmark.open("test")
        assert exc_info.value == error

    def test_create_already_exists_loads_existing(self, mocked_usecases: dict[str, MagicMock]) -> None:
        benchmark_entity = BenchmarkEntity(name="test", modelset=None, features=[], algorithms=[], metrics=[], plots=[])
        mock_create = mocked_usecases["benchmark_create_uc"]
        mock_load = mocked_usecases["benchmark_load_uc"]
        mock_create.return_value = Failure(DataNotUniqueError())
        mock_load.return_value = Success(benchmark_entity)

        b = Benchmark.create("test")
        assert b.model_dump() == benchmark_entity.model_dump()
        mock_load.assert_called_once_with("test")

    def test_add_feature_already_exists_returns_existing(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        feature_entity = FeatureEntity(name="feat", feature=MockFeature(), results={})
        empty_benchmark.features.append(feature_entity)
        mocked_usecases["benchmark_add_feature_uc"].return_value = Failure(DataNotUniqueError())

        result = empty_benchmark.add_feature("feat", MagicMock())
        assert result.model_dump() == feature_entity.model_dump()

    def test_add_metric_already_exists_returns_existing(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        metric_entity = MetricEntity(name="met", metric=MockMetric(), results={})
        empty_benchmark.metrics.append(metric_entity)
        mocked_usecases["benchmark_add_metric_uc"].return_value = Failure(DataNotUniqueError())

        result = empty_benchmark.add_metric("met", MagicMock())
        assert result.model_dump() == metric_entity.model_dump()

    def test_add_algorithm_already_exists_returns_existing(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        algorithm_entity = AlgorithmEntity(name="algo", algorithm=MockAlgorithm(), results={})
        empty_benchmark.algorithms.append(algorithm_entity)
        mocked_usecases["benchmark_add_algorithm_uc"].return_value = Failure(DataNotUniqueError())

        result = empty_benchmark.add_algorithm("algo", MagicMock())
        assert result.model_dump() == algorithm_entity.model_dump()

    def test_add_plot_already_exists_returns_existing(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        plot_entity = PlotEntity(name="plot", plot=MockPlot())
        empty_benchmark.plots.append(plot_entity)
        mocked_usecases["benchmark_add_plot_uc"].return_value = Failure(DataNotUniqueError())

        result = empty_benchmark.add_plot("plot", MagicMock())
        assert result.model_dump() == plot_entity.model_dump()

    @pytest.fixture()
    def benchmark_with_entries(self) -> Benchmark:
        feature_entity = FeatureEntity(name="feat", feature=MockFeature(), results={})
        metric_entity = MetricEntity(name="met", metric=MockMetric(), results={})
        algorithm_entity = AlgorithmEntity(name="algo", algorithm=MockAlgorithm(), results={})
        plot_entity = PlotEntity(name="plot", plot=MockPlot())
        return Benchmark.model_construct(
            name="test",
            modelset=None,
            features=[feature_entity],
            algorithms=[algorithm_entity],
            metrics=[metric_entity],
            plots=[plot_entity],
        )

    @pytest.mark.parametrize(
        ("getter", "existing_name"),
        [
            ("get_feature", "feat"),
            ("get_metric", "met"),
            ("get_algorithm", "algo"),
            ("get_plot", "plot"),
        ],
    )
    def test_get_existing(self, getter: str, existing_name: str, benchmark_with_entries: Benchmark) -> None:
        result = getattr(benchmark_with_entries, getter)(existing_name)
        assert result.name == existing_name

    @pytest.mark.parametrize("getter", ["get_feature", "get_metric", "get_algorithm", "get_plot"])
    def test_get_missing_raises(self, getter: str, benchmark_with_entries: Benchmark) -> None:
        with pytest.raises(DataNotExistError):
            getattr(benchmark_with_entries, getter)("missing")

    def test_add_dependencies_plot_requires_metric(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        """Test that add_dependencies adds metrics required by plots."""
        mock_plot = MagicMock(spec=MockPlot)
        mock_plot.required_metrics = [MockMetric]
        mock_plot.required_features = []

        plot_entity = PlotEntity(name="plot_with_deps", plot=mock_plot)
        empty_benchmark.plots.append(plot_entity)

        metric_entity = MetricEntity(name="mock_metric", metric=MockMetric(), results={})
        mocked_usecases["benchmark_add_metric_uc"].return_value = Success(metric_entity)

        empty_benchmark.add_dependencies()

        assert len(empty_benchmark.metrics) == 1
        assert empty_benchmark.metrics[0].name == "mock_metric"
        mocked_usecases["benchmark_add_metric_uc"].assert_called_once()

    def test_add_dependencies_plot_requires_feature(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        """Test that add_dependencies adds features required by plots."""
        mock_plot = MagicMock(spec=MockPlot)
        mock_plot.required_metrics = []
        mock_plot.required_features = [MockFeature]

        plot_entity = PlotEntity(name="plot_with_deps", plot=mock_plot)
        empty_benchmark.plots.append(plot_entity)

        feature_entity = FeatureEntity(name="mock_feature", feature=MockFeature(), results={})
        mocked_usecases["benchmark_add_feature_uc"].return_value = Success(feature_entity)

        empty_benchmark.add_dependencies()

        assert len(empty_benchmark.features) == 1
        assert empty_benchmark.features[0].name == "mock_feature"
        mocked_usecases["benchmark_add_feature_uc"].assert_called_once()

    def test_add_dependencies_metric_requires_feature(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        """Test that add_dependencies adds features required by metrics."""
        mock_metric = MagicMock(spec=MockMetric)
        mock_metric.required_features = [MockFeature]

        metric_entity = MetricEntity(name="metric_with_deps", metric=mock_metric, results={})
        empty_benchmark.metrics.append(metric_entity)

        feature_entity = FeatureEntity(name="mock_feature", feature=MockFeature(), results={})
        mocked_usecases["benchmark_add_feature_uc"].return_value = Success(feature_entity)

        empty_benchmark.add_dependencies()

        assert len(empty_benchmark.features) == 1
        assert empty_benchmark.features[0].name == "mock_feature"
        mocked_usecases["benchmark_add_feature_uc"].assert_called_once()

    def test_add_dependencies_skips_existing_components(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        """Test that add_dependencies doesn't add components that already exist."""
        mock_plot = MagicMock(spec=MockPlot)
        mock_plot.required_metrics = [MockMetric]
        mock_plot.required_features = []

        existing_metric_entity = MetricEntity(name="mock_metric", metric=MockMetric(), results={})
        plot_entity = PlotEntity(name="plot_with_deps", plot=mock_plot)

        empty_benchmark.metrics.append(existing_metric_entity)
        empty_benchmark.plots.append(plot_entity)

        empty_benchmark.add_dependencies()

        mocked_usecases["benchmark_add_metric_uc"].assert_not_called()

    def test_add_dependencies_nested_dependencies(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        """Test that add_dependencies handles nested dependencies correctly."""
        mock_metric = MagicMock(spec=MockMetric)
        mock_metric.required_features = [MockFeature]

        mock_plot = MagicMock(spec=MockPlot)
        mock_plot.required_metrics = [MockMetric]
        mock_plot.required_features = []

        plot_entity = PlotEntity(name="plot_with_deps", plot=mock_plot)
        empty_benchmark.plots.append(plot_entity)

        metric_entity = MetricEntity(name="mock_metric", metric=mock_metric, results={})
        feature_entity = FeatureEntity(name="mock_feature", feature=MockFeature(), results={})

        mocked_usecases["benchmark_add_metric_uc"].return_value = Success(metric_entity)
        mocked_usecases["benchmark_add_feature_uc"].return_value = Success(feature_entity)

        empty_benchmark.add_dependencies()

        assert len(empty_benchmark.metrics) == 1
        assert len(empty_benchmark.features) == 1
        mocked_usecases["benchmark_add_metric_uc"].assert_called_once()
        mocked_usecases["benchmark_add_feature_uc"].assert_called_once()

    def test_add_model_creates_modelset_named_after_benchmark(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mocked_usecases["modelset_create_uc"].return_value = Success(
            ModelSetEntity(id=1, name=empty_benchmark.name, models=[])
        )
        mocked_usecases["benchmark_set_modelset_uc"].return_value = Success(None)
        mocked_usecases["model_add_uc"].return_value = Success(
            ModelSetEntity(id=1, name=empty_benchmark.name, models=[])
        )
        model = simple_model("m1")

        empty_benchmark.add_model(model)

        mocked_usecases["modelset_create_uc"].assert_called_once_with(modelset_name="test")
        mocked_usecases["benchmark_set_modelset_uc"].assert_called_once_with("test", "test")
        mocked_usecases["model_add_uc"].assert_called_once_with(modelset_name="test", model=model)

    def test_add_model_says_so_when_it_adopts_a_modelset_that_already_has_models(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark, caplog: pytest.LogCaptureFixture
    ) -> None:
        # ModelSet.create falls back to loading when the name is taken, so a
        # benchmark with no modelset can pick up one that is already populated.
        model = simple_model("m1")
        existing = ModelSetEntity(
            id=1, name=empty_benchmark.name, models=[ModelMetadataEntity(id=1, name="older", hash=1)]
        )
        mocked_usecases["modelset_create_uc"].return_value = Failure(DataNotUniqueError())
        mocked_usecases["modelset_load_uc"].return_value = Success(existing)
        mocked_usecases["benchmark_set_modelset_uc"].return_value = Success(None)
        mocked_usecases["model_add_uc"].return_value = Success(existing)

        with caplog.at_level(logging.WARNING):
            empty_benchmark.add_model(model)

        assert "test" in caplog.text
        assert "older" in caplog.text
        assert "adopt" in caplog.text.lower()

    def test_add_model_is_quiet_when_the_adopted_modelset_is_empty(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark, caplog: pytest.LogCaptureFixture
    ) -> None:
        empty = ModelSetEntity(id=1, name=empty_benchmark.name, models=[])
        mocked_usecases["modelset_create_uc"].return_value = Failure(DataNotUniqueError())
        mocked_usecases["modelset_load_uc"].return_value = Success(empty)
        mocked_usecases["benchmark_set_modelset_uc"].return_value = Success(None)
        mocked_usecases["model_add_uc"].return_value = Success(empty)

        with caplog.at_level(logging.WARNING):
            empty_benchmark.add_model(simple_model("m1"))

        assert "adopt" not in caplog.text.lower()

    def test_add_model_uses_live_modelset_without_reloading(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        live_modelset = MagicMock(spec=ModelSet)
        live_modelset.name = "existing_set"
        empty_benchmark.modelset = live_modelset
        model = simple_model("m1")

        empty_benchmark.add_model(model)

        live_modelset.add.assert_called_once_with(model)
        mocked_usecases["modelset_create_uc"].assert_not_called()
        mocked_usecases["modelset_load_uc"].assert_not_called()

    def test_add_model_with_iterable_delegates_whole_iterable(self, empty_benchmark: Benchmark) -> None:
        live_modelset = MagicMock(spec=ModelSet)
        live_modelset.name = "existing_set"
        empty_benchmark.modelset = live_modelset
        models = [simple_model("m1"), simple_model("m2")]

        empty_benchmark.add_model(models)

        live_modelset.add.assert_called_once_with(models)

    def test_add_model_promotes_a_data_only_modelset(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        modelset_entity = ModelSetEntity(id=1, name="loaded_set", models=[])
        empty_benchmark.modelset = modelset_entity
        mocked_usecases["modelset_load_uc"].return_value = Success(modelset_entity)
        mocked_usecases["model_add_uc"].return_value = Success(modelset_entity)
        model = simple_model("m1")

        empty_benchmark.add_model(model)

        mocked_usecases["modelset_load_uc"].assert_called_once_with(modelset_name="loaded_set")
        mocked_usecases["model_add_uc"].assert_called_once_with(modelset_name="loaded_set", model=model)
        assert isinstance(empty_benchmark.modelset, ModelSet)
        mocked_usecases["modelset_create_uc"].assert_not_called()

    def test_add_model_raises_when_the_modelset_cannot_be_loaded(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        empty_benchmark.modelset = ModelSetEntity(id=1, name="loaded_set", models=[])
        mocked_usecases["modelset_load_uc"].return_value = Failure(DataNotExistError())

        with pytest.raises(ModelSetNotLoadedError) as exc_info:
            empty_benchmark.add_model(simple_model("m1"))

        assert exc_info.value.benchmark_name == "test"
        assert exc_info.value.modelset_name == "loaded_set"
        mocked_usecases["model_add_uc"].assert_not_called()

    def test_remove_model_delegates_to_live_modelset(self, empty_benchmark: Benchmark) -> None:
        live_modelset = MagicMock(spec=ModelSet)
        live_modelset.name = "existing_set"
        empty_benchmark.modelset = live_modelset
        model = simple_model("m1")

        empty_benchmark.remove_model(model)

        live_modelset.remove_model.assert_called_once_with(model)

    def test_remove_model_with_iterable_delegates_whole_iterable(self, empty_benchmark: Benchmark) -> None:
        live_modelset = MagicMock(spec=ModelSet)
        live_modelset.name = "existing_set"
        empty_benchmark.modelset = live_modelset
        models = [simple_model("m1"), simple_model("m2")]

        empty_benchmark.remove_model(models)

        live_modelset.remove_model.assert_called_once_with(models)

    def test_remove_model_without_modelset_raises(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        with pytest.raises(DataNotExistError) as exc_info:
            empty_benchmark.remove_model(simple_model("m1"))

        # The generic "requested data does not exist" says nothing useful here.
        assert "test" in str(exc_info.value)
        assert "modelset" in str(exc_info.value)
        mocked_usecases["modelset_create_uc"].assert_not_called()
        mocked_usecases["model_remove_uc"].assert_not_called()

    def test_remove_model_promotes_a_data_only_modelset(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        model = simple_model("m1")
        modelset_entity = ModelSetEntity(
            id=1, name="loaded_set", models=[ModelMetadataEntity(id=1, name="m1", hash=model.__hash__())]
        )
        empty_benchmark.modelset = modelset_entity
        mocked_usecases["modelset_load_uc"].return_value = Success(modelset_entity)
        mocked_usecases["model_remove_uc"].return_value = Success(ModelSetEntity(id=1, name="loaded_set", models=[]))

        empty_benchmark.remove_model(model)

        mocked_usecases["modelset_load_uc"].assert_called_once_with(modelset_name="loaded_set")
        mocked_usecases["model_remove_uc"].assert_called_once_with(modelset_name="loaded_set", model=model)

    def test_remove_model_raises_when_the_modelset_cannot_be_loaded(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        empty_benchmark.modelset = ModelSetEntity(id=1, name="loaded_set", models=[])
        mocked_usecases["modelset_load_uc"].return_value = Failure(DataNotExistError())

        with pytest.raises(ModelSetNotLoadedError) as exc_info:
            empty_benchmark.remove_model(simple_model("m1"))

        assert exc_info.value.modelset_name == "loaded_set"
        mocked_usecases["model_remove_uc"].assert_not_called()

    def test_load_promotes_a_data_only_modelset_to_a_live_handle(self, mocked_usecases: dict[str, MagicMock]) -> None:
        modelset_entity = ModelSetEntity(id=1, name="loaded_set", models=[])
        mocked_usecases["benchmark_load_uc"].return_value = Success(
            BenchmarkEntity(name="test", modelset=modelset_entity, features=[], algorithms=[], metrics=[], plots=[])
        )
        mocked_usecases["modelset_load_uc"].return_value = Success(modelset_entity)

        benchmark = Benchmark.load("test")

        assert isinstance(benchmark.modelset, ModelSet)
        mocked_usecases["modelset_load_uc"].assert_called_once_with(modelset_name="loaded_set")

    def test_open_promotes_a_data_only_modelset_to_a_live_handle(self, mocked_usecases: dict[str, MagicMock]) -> None:
        modelset_entity = ModelSetEntity(id=1, name="loaded_set", models=[])
        mocked_usecases["benchmark_load_uc"].return_value = Success(
            BenchmarkEntity(name="test", modelset=modelset_entity, features=[], algorithms=[], metrics=[], plots=[])
        )
        mocked_usecases["modelset_load_uc"].return_value = Success(modelset_entity)

        benchmark = Benchmark.open("test")

        assert isinstance(benchmark.modelset, ModelSet)

    def test_load_keeps_going_when_the_modelset_cannot_be_loaded(
        self, mocked_usecases: dict[str, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        modelset_entity = ModelSetEntity(id=1, name="vanished_set", models=[])
        mocked_usecases["benchmark_load_uc"].return_value = Success(
            BenchmarkEntity(name="test", modelset=modelset_entity, features=[], algorithms=[], metrics=[], plots=[])
        )
        mocked_usecases["modelset_load_uc"].return_value = Failure(DataNotExistError())

        with caplog.at_level(logging.WARNING):
            benchmark = Benchmark.load("test")

        assert benchmark.modelset is not None
        assert not isinstance(benchmark.modelset, ModelSet)
        assert "vanished_set" in caplog.text


class TestToDataframe:
    @staticmethod
    def _make_benchmark(
        features: list[FeatureEntity] | None = None,
        metrics: list[MetricEntity] | None = None,
        algorithms: list[AlgorithmEntity] | None = None,
    ) -> Benchmark:
        return Benchmark.model_construct(
            name="test",
            modelset=None,
            features=features or [],
            algorithms=algorithms or [],
            metrics=metrics or [],
            plots=[],
        )

    def test_empty_benchmark_raises_error(self) -> None:
        benchmark = self._make_benchmark()
        with pytest.raises(ValueError, match="no algorithm results available"):
            benchmark.to_dataframe()

    def test_features_and_metrics(self) -> None:
        feature = make_feature_entity("num_vars", ("model1", {"count": 42}))
        metric = make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))
        algo = make_algo_entity("algo1", ["model1"])
        benchmark = self._make_benchmark(features=[feature], metrics=[metric], algorithms=[algo])
        df = benchmark.to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["algorithm"] == "algo1"
        assert df.iloc[0]["num_vars/count"] == 42
        assert df.iloc[0]["accuracy/score"] == 0.95

    def test_none_result_is_na(self) -> None:
        metric_success = make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))
        metric_fail = make_metric_entity(
            "accuracy",
            ("algo2", "model1", {}),
            status=JobStatus.FAILED,
            error="something went wrong",
        )
        algo1 = make_algo_entity("algo1", ["model1"])
        algo2 = make_algo_entity("algo2", ["model1"])
        benchmark = self._make_benchmark(metrics=[metric_success, metric_fail], algorithms=[algo1, algo2])
        df = benchmark.to_dataframe()
        assert len(df) == 2
        assert df.iloc[0]["accuracy/score"] == 0.95
        assert pd.isna(df.iloc[1]["accuracy/score"])

    def test_multiple_metrics_same_algorithm_model(self) -> None:
        metric1 = make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))
        metric2 = make_metric_entity("runtime", ("algo1", "model1", {"seconds": 1.23}))
        algo = make_algo_entity("algo1", ["model1"])
        benchmark = self._make_benchmark(metrics=[metric1, metric2], algorithms=[algo])
        df = benchmark.to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["accuracy/score"] == 0.95
        assert df.iloc[0]["runtime/seconds"] == 1.23

    def test_feature_repeated_across_algorithms(self) -> None:
        feature = make_feature_entity("size", ("model1", {"value": 10}))
        metric = make_metric_entity(
            "accuracy",
            ("algo1", "model1", {"score": 0.9}),
            ("algo2", "model1", {"score": 0.8}),
        )
        algo1 = make_algo_entity("algo1", ["model1"])
        algo2 = make_algo_entity("algo2", ["model1"])
        benchmark = self._make_benchmark(features=[feature], metrics=[metric], algorithms=[algo1, algo2])
        df = benchmark.to_dataframe()

        assert len(df) == 2
        assert df.iloc[0]["size/value"] == 10
        assert df.iloc[1]["size/value"] == 10
        assert df.iloc[0]["accuracy/score"] == 0.9
        assert df.iloc[1]["accuracy/score"] == 0.8


class TestExport:
    @staticmethod
    def _make_benchmark(
        features: list[FeatureEntity] | None = None,
        metrics: list[MetricEntity] | None = None,
        algorithms: list[AlgorithmEntity] | None = None,
    ) -> Benchmark:
        return Benchmark.model_construct(
            name="test",
            modelset=None,
            features=features or [],
            algorithms=algorithms or [],
            metrics=metrics or [],
            plots=[],
        )

    @staticmethod
    def _default_benchmark() -> Benchmark:
        return TestExport._make_benchmark(
            features=[make_feature_entity("num_vars", ("model1", {"count": 42}))],
            metrics=[make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))],
            algorithms=[make_algo_entity("algo1", ["model1"])],
        )

    def test_export_passes_full_container_to_exporter(self) -> None:
        captured: list[BenchmarkResultContainer] = []

        class CapturingExporter:
            def export(self, benchmark_results: BenchmarkResultContainer) -> str:
                captured.append(benchmark_results)
                return "payload"

        result = self._default_benchmark().export(CapturingExporter())

        assert result == "payload"
        container = captured[0]
        assert set(container.features) == {"model1"}
        assert set(container.metrics["model1"]) == {"algo1"}
        assert set(container.algorithms["model1"]) == {"algo1"}

    def test_export_with_dataframe_exporter_matches_to_dataframe(self) -> None:
        benchmark = self._default_benchmark()

        via_export = benchmark.export(DataFrameExporter())
        via_method = benchmark.to_dataframe()

        pd.testing.assert_frame_equal(via_export, via_method)

    def test_to_csv(self) -> None:
        csv_str = self._default_benchmark().to_csv()
        assert csv_str is not None
        header, row = csv_str.strip().split("\n")

        assert header == "algorithm,model,meta_data,algorithm_config,accuracy/score,num_vars/count"
        assert row.startswith("algo1,model1,")

    def test_to_csv_with_options(self) -> None:
        csv_str = self._default_benchmark().to_csv(delimiter=";", quoting="all")
        assert csv_str is not None

        assert csv_str.startswith('"algorithm";"model";')

    def test_to_json(self) -> None:
        json_str = self._default_benchmark().to_json()
        assert json_str is not None
        records = json.loads(json_str)

        assert records == [
            {
                "algorithm": "algo1",
                "model": "model1",
                "meta_data": None,
                "algorithm_config": {},
                "accuracy/score": 0.95,
                "num_vars/count": 42,
            }
        ]

    def test_to_csv_writes_file_when_path_given(self, tmp_path: Path) -> None:
        benchmark = self._default_benchmark()
        target = tmp_path / "results.csv"

        result = benchmark.to_csv(target)

        assert result is None
        assert target.read_text(encoding="utf-8") == benchmark.to_csv()

    def test_to_json_writes_file_when_path_given(self, tmp_path: Path) -> None:
        benchmark = self._default_benchmark()
        target = tmp_path / "results.json"

        result = benchmark.to_json(str(target))

        assert result is None
        assert target.read_text(encoding="utf-8") == benchmark.to_json()

    def test_export_empty_benchmark_raises_for_dataframe_exporter(self) -> None:
        with pytest.raises(ValueError, match="no algorithm results available"):
            self._make_benchmark().export(DataFrameExporter())


class TestListClasses:
    def _make_benchmark(
        self,
        features: list[FeatureEntity] | None = None,
        metrics: list[MetricEntity] | None = None,
        algorithms: list[AlgorithmEntity] | None = None,
        plots: list[PlotEntity] | None = None,
    ) -> Benchmark:
        return Benchmark.model_construct(
            name="test",
            modelset=None,
            features=features or [],
            algorithms=algorithms or [],
            metrics=metrics or [],
            plots=plots or [],
        )

    def test_list_feature_classes(self) -> None:
        f1 = FeatureEntity(name="f1", feature=MockFeature(), results={})
        f2 = FeatureEntity(name="f2", feature=MockFeature(), results={})
        benchmark = self._make_benchmark(features=[f1, f2])

        result = benchmark.list_feature_classes()

        assert len(result) == 2
        assert all(issubclass(c, MockFeature) for c in result)

    def test_list_metrics_classes(self) -> None:
        m1 = MetricEntity(name="acc", metric=MockMetric(), results={})
        m2 = MetricEntity(name="loss", metric=MockMetric(), results={})
        benchmark = self._make_benchmark(metrics=[m1, m2])

        result = benchmark.list_metrics_classes()

        assert len(result) == 2
        assert all(issubclass(c, MockMetric) for c in result)

    def test_list_plots_classes(self) -> None:
        p1 = PlotEntity(name="plot1", plot=MockPlot())
        p2 = PlotEntity(name="plot2", plot=MockPlot())
        benchmark = self._make_benchmark(plots=[p1, p2])

        result = benchmark.list_plots_classes()

        assert len(result) == 2
        assert all(issubclass(c, MockPlot) for c in result)

    def test_list_algorithms(self) -> None:
        a1 = AlgorithmEntity(name="algo1", algorithm=MockAlgorithm(), results={})
        a2 = AlgorithmEntity(name="algo2", algorithm=MockAlgorithm(), results={})
        benchmark = self._make_benchmark(algorithms=[a1, a2])

        result = benchmark.list_algorithms()

        assert len(result) == 2
        assert all(issubclass(c, MockAlgorithm) for c, _ in result)

    @pytest.mark.parametrize(
        "method",
        ["list_feature_classes", "list_metrics_classes", "list_plots_classes", "list_algorithms"],
    )
    def test_list_classes_empty(self, method: str) -> None:
        benchmark = self._make_benchmark()
        assert getattr(benchmark, method)() == []


class TestPlotSummary:
    """Test the convenience wrapper around the standalone summary function."""

    @staticmethod
    def _make_benchmark(data_dir_plots: str | None = "plots_dir") -> Benchmark:
        return Benchmark.model_construct(
            name="test",
            modelset=None,
            features=[],
            algorithms=[],
            metrics=[],
            plots=[],
            data_dir_plots=data_dir_plots,
        )

    def test_it_forwards_to_the_standalone_function(self) -> None:
        benchmark = self._make_benchmark()

        with patch("luna_bench.plots.plot_summary") as mock_summary:
            result = benchmark.plot_summary(columns=3, rows=2, show=False, title="Run 3")

        assert result is mock_summary.return_value
        mock_summary.assert_called_once_with(
            benchmark,
            columns=3,
            rows=2,
            save_dir="plots_dir",
            figure_filename="summary",
            file_formats=("png",),
            show=False,
            title="Run 3",
        )

    def test_save_dir_defaults_to_the_benchmark_plots_directory(self) -> None:
        benchmark = self._make_benchmark(data_dir_plots="/tmp/bench/plots")

        with patch("luna_bench.plots.plot_summary") as mock_summary:
            benchmark.plot_summary()

        assert mock_summary.call_args.kwargs["save_dir"] == "/tmp/bench/plots"

    def test_an_explicit_save_dir_wins(self) -> None:
        benchmark = self._make_benchmark()

        with patch("luna_bench.plots.plot_summary") as mock_summary:
            benchmark.plot_summary(save_dir="elsewhere")

        assert mock_summary.call_args.kwargs["save_dir"] == "elsewhere"
