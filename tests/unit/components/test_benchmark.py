from collections.abc import Generator
from contextlib import ExitStack
from unittest.mock import MagicMock

import pytest
from returns.result import Failure, Success

from luna_bench.components.benchmark import Benchmark
from luna_bench.components.model_set import ModelSet
from luna_bench.entities import (
    AlgorithmEntity,
    AlgorithmResultEntity,
    BenchmarkEntity,
    ErrorHandlingMode,
    FeatureEntity,
    FeatureResultEntity,
    JobStatus,
    MetricEntity,
    MetricResultEntity,
    PlotEntity,
)
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.types import FeatureResult, MetricResult
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric, MockPlot


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
        feature_entity = FeatureEntity(name="feat", status=JobStatus.CREATED, feature=MockFeature(), results={})
        mock_add.return_value = Success(feature_entity)

        res = empty_benchmark.add_feature("feat", MagicMock())
        assert res.model_dump() == feature_entity.model_dump()
        assert len(empty_benchmark.features) == 1
        assert empty_benchmark.features[0].model_dump() == feature_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            DataNotUniqueError(),
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_add_feature_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_add = mocked_usecases["benchmark_add_feature_uc"]
        mock_add.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.add_feature("feat", MagicMock())
        assert exc_info.value == error

    def test_add_algorithm_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_algorithm_uc"]
        algorithm_entity = AlgorithmEntity(name="algo", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={})
        mock_add.return_value = Success(algorithm_entity)

        res = empty_benchmark.add_algorithm("algo", MagicMock())
        assert res.model_dump() == algorithm_entity.model_dump()
        assert len(empty_benchmark.algorithms) == 1
        assert empty_benchmark.algorithms[0].model_dump() == algorithm_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            DataNotUniqueError(),
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_add_algorithm_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_add = mocked_usecases["benchmark_add_algorithm_uc"]
        mock_add.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.add_algorithm("algo", MagicMock())
        assert exc_info.value == error

    def test_add_metric_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_metric_uc"]
        metric_entity = MetricEntity(name="met", status=JobStatus.CREATED, metric=MockMetric(), results={})
        mock_add.return_value = Success(metric_entity)

        res = empty_benchmark.add_metric("met", MagicMock())
        assert res.model_dump() == metric_entity.model_dump()
        assert len(empty_benchmark.metrics) == 1
        assert empty_benchmark.metrics[0].model_dump() == metric_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            DataNotUniqueError(),
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_add_metric_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_add = mocked_usecases["benchmark_add_metric_uc"]
        mock_add.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.add_metric("met", MagicMock())
        assert exc_info.value == error

    def test_add_plot_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_add = mocked_usecases["benchmark_add_plot_uc"]
        plot_entity = PlotEntity(name="plot", status=JobStatus.CREATED, plot=MockPlot())
        mock_add.return_value = Success(plot_entity)

        res = empty_benchmark.add_plot("plot", MagicMock())
        assert res.model_dump() == plot_entity.model_dump()
        assert len(empty_benchmark.plots) == 1
        assert empty_benchmark.plots[0].model_dump() == plot_entity.model_dump()

    @pytest.mark.parametrize(
        "error",
        [
            DataNotUniqueError(),
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_add_plot_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_add = mocked_usecases["benchmark_add_plot_uc"]
        mock_add.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.add_plot("plot", MagicMock())
        assert exc_info.value == error

    def test_set_modelset_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        mock_set = mocked_usecases["benchmark_set_modelset_uc"]
        mock_set.return_value = Success(None)

        modelset = MagicMock(spec=ModelSet)
        modelset.name = "test_modelset"
        empty_benchmark.set_modelset(modelset)
        assert empty_benchmark.modelset == modelset
        mock_set.assert_called_once_with(empty_benchmark.name, "test_modelset")

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
        feature_entity = FeatureEntity(name="feat", status=JobStatus.CREATED, feature=MockFeature(), results={})
        empty_benchmark.features.append(feature_entity)

        mock_remove = mocked_usecases["benchmark_remove_feature_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_feature("feat")
        assert len(empty_benchmark.features) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "feat")

    def test_remove_metric_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        metric_entity = MetricEntity(name="met", status=JobStatus.CREATED, metric=MockMetric(), results={})
        empty_benchmark.metrics.append(metric_entity)

        mock_remove = mocked_usecases["benchmark_remove_metric_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_metric("met")
        assert len(empty_benchmark.metrics) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "met")

    def test_remove_algorithm_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        algorithm_entity = AlgorithmEntity(name="algo", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={})
        empty_benchmark.algorithms.append(algorithm_entity)

        mock_remove = mocked_usecases["benchmark_remove_algorithm_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_algorithm("algo")
        assert len(empty_benchmark.algorithms) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "algo")

    def test_remove_plot_success(self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark) -> None:
        plot_entity = PlotEntity(name="plot", status=JobStatus.CREATED, plot=MockPlot())
        empty_benchmark.plots.append(plot_entity)

        mock_remove = mocked_usecases["benchmark_remove_plot_uc"]
        mock_remove.return_value = Success(None)

        empty_benchmark.remove_plot("plot")
        assert len(empty_benchmark.plots) == 0
        mock_remove.assert_called_once_with(empty_benchmark.name, "plot")

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_remove_feature_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_remove = mocked_usecases["benchmark_remove_feature_uc"]
        mock_remove.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.remove_feature("feat")
        assert exc_info.value == error

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_remove_metric_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_remove = mocked_usecases["benchmark_remove_metric_uc"]
        mock_remove.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.remove_metric("met")
        assert exc_info.value == error

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_remove_algorithm_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_remove = mocked_usecases["benchmark_remove_algorithm_uc"]
        mock_remove.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.remove_algorithm("algo")
        assert exc_info.value == error

    @pytest.mark.parametrize(
        "error",
        [
            DataNotExistError(),
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_remove_plot_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock_remove = mocked_usecases["benchmark_remove_plot_uc"]
        mock_remove.return_value = Failure(error)
        if isinstance(error, UnknownLunaBenchError):
            error = error.error()

        with pytest.raises(type(error)) as exc_info:
            empty_benchmark.remove_plot("plot")
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

        # default is FAIL_ON_ERROR = 0
        args, _ = mock.call_args
        assert args[0] == empty_benchmark
        assert args[1].value == ErrorHandlingMode.FAIL_ON_ERROR.value

    def test_run_plots_continue_on_error(
        self, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
        mock = mocked_usecases["benchmark_run_plots_uc"]
        mock.return_value = Success(None)
        empty_benchmark.run_plots(ErrorHandlingMode.CONTINUE_ON_ERROR)

        args, _ = mock.call_args
        assert args[0] == empty_benchmark
        assert args[1].value == ErrorHandlingMode.CONTINUE_ON_ERROR.value

    @pytest.mark.parametrize(
        "error",
        [
            UnknownLunaBenchError(exception=RuntimeError("another error")),
        ],
    )
    def test_run_plots_failure(
        self, error: Exception, mocked_usecases: dict[str, MagicMock], empty_benchmark: Benchmark
    ) -> None:
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
        assert args[1].value == ErrorHandlingMode.FAIL_ON_ERROR.value


class TestResultsToDataframe:
    def _make_benchmark(
        self,
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

    def test_empty_benchmark_returns_empty_dataframe(self) -> None:
        benchmark = self._make_benchmark()
        df = benchmark.results_to_dataframe()
        assert df.empty
        assert len(df.columns) == 0

    def test_metrics_only(self) -> None:
        metric_entity = MetricEntity(
            name="accuracy",
            status=JobStatus.DONE,
            metric=MockMetric(),
            results={
                ("algo1", "model1"): MetricResultEntity(
                    processing_time_ms=100,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(score=0.95),  # type: ignore[call-arg]
                ),
                ("algo1", "model2"): MetricResultEntity(
                    processing_time_ms=120,
                    model_name="model2",
                    algorithm_name="algo1",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(score=0.87),  # type: ignore[call-arg]
                ),
            },
        )
        benchmark = self._make_benchmark(metrics=[metric_entity])
        df = benchmark.results_to_dataframe()

        assert len(df) == 2
        assert list(df.columns) == ["algorithm", "model", "accuracy/score"]
        assert df.iloc[0]["algorithm"] == "algo1"
        assert df.iloc[0]["accuracy/score"] == 0.95

    def test_features_and_metrics(self) -> None:
        feature_entity = FeatureEntity(
            name="num_vars",
            status=JobStatus.DONE,
            feature=MockFeature(),
            results={
                "model1": FeatureResultEntity(
                    processing_time_ms=10,
                    model_name="model1",
                    status=JobStatus.DONE,
                    error=None,
                    result=FeatureResult.model_construct(count=42),  # type: ignore[call-arg]
                ),
            },
        )
        metric_entity = MetricEntity(
            name="accuracy",
            status=JobStatus.DONE,
            metric=MockMetric(),
            results={
                ("algo1", "model1"): MetricResultEntity(
                    processing_time_ms=100,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(score=0.95),  # type: ignore[call-arg]
                ),
            },
        )
        benchmark = self._make_benchmark(features=[feature_entity], metrics=[metric_entity])
        df = benchmark.results_to_dataframe()

        assert len(df) == 1
        assert "num_vars/count" in df.columns
        assert "accuracy/score" in df.columns
        assert df.iloc[0]["num_vars/count"] == 42
        assert df.iloc[0]["accuracy/score"] == 0.95

    def test_none_result_is_skipped(self) -> None:
        metric_entity = MetricEntity(
            name="accuracy",
            status=JobStatus.DONE,
            metric=MockMetric(),
            results={
                ("algo1", "model1"): MetricResultEntity(
                    processing_time_ms=100,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=JobStatus.FAILED,
                    error="something went wrong",
                    result=None,
                ),
            },
        )
        benchmark = self._make_benchmark(metrics=[metric_entity])
        df = benchmark.results_to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["algorithm"] == "algo1"
        assert "accuracy/score" not in df.columns

    def test_multiple_metrics_same_algorithm_model(self) -> None:
        metric1 = MetricEntity(
            name="accuracy",
            status=JobStatus.DONE,
            metric=MockMetric(),
            results={
                ("algo1", "model1"): MetricResultEntity(
                    processing_time_ms=100,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(score=0.95),  # type: ignore[call-arg]
                ),
            },
        )
        metric2 = MetricEntity(
            name="runtime",
            status=JobStatus.DONE,
            metric=MockMetric(),
            results={
                ("algo1", "model1"): MetricResultEntity(
                    processing_time_ms=50,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(seconds=1.23),  # type: ignore[call-arg]
                ),
            },
        )
        benchmark = self._make_benchmark(metrics=[metric1, metric2])
        df = benchmark.results_to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["accuracy/score"] == 0.95
        assert df.iloc[0]["runtime/seconds"] == 1.23

    def test_fallback_to_algorithms_when_no_metrics(self) -> None:
        feature_entity = FeatureEntity(
            name="num_vars",
            status=JobStatus.DONE,
            feature=MockFeature(),
            results={
                "model1": FeatureResultEntity(
                    processing_time_ms=10,
                    model_name="model1",
                    status=JobStatus.DONE,
                    error=None,
                    result=FeatureResult.model_construct(count=42),  # type: ignore[call-arg]
                ),
            },
        )
        algo_entity = AlgorithmEntity(
            name="algo1",
            status=JobStatus.DONE,
            algorithm=MockAlgorithm(),
            results={
                "model1": AlgorithmResultEntity(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=None,
                    task_id=None,
                    retrival_data=None,
                    model_id=1,
                ),
            },
        )
        benchmark = self._make_benchmark(features=[feature_entity], algorithms=[algo_entity])
        df = benchmark.results_to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["algorithm"] == "algo1"
        assert df.iloc[0]["model"] == "model1"
        assert df.iloc[0]["num_vars/count"] == 42

    def test_feature_repeated_across_algorithms(self) -> None:
        feature_entity = FeatureEntity(
            name="size",
            status=JobStatus.DONE,
            feature=MockFeature(),
            results={
                "model1": FeatureResultEntity(
                    processing_time_ms=5,
                    model_name="model1",
                    status=JobStatus.DONE,
                    error=None,
                    result=FeatureResult.model_construct(value=10),  # type: ignore[call-arg]
                ),
            },
        )
        metric_entity = MetricEntity(
            name="accuracy",
            status=JobStatus.DONE,
            metric=MockMetric(),
            results={
                ("algo1", "model1"): MetricResultEntity(
                    processing_time_ms=100,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(score=0.9),  # type: ignore[call-arg]
                ),
                ("algo2", "model1"): MetricResultEntity(
                    processing_time_ms=110,
                    model_name="model1",
                    algorithm_name="algo2",
                    status=JobStatus.DONE,
                    error=None,
                    result=MetricResult.model_construct(score=0.8),  # type: ignore[call-arg]
                ),
            },
        )
        benchmark = self._make_benchmark(features=[feature_entity], metrics=[metric_entity])
        df = benchmark.results_to_dataframe()

        assert len(df) == 2
        assert df.iloc[0]["size/value"] == 10
        assert df.iloc[1]["size/value"] == 10
        assert df.iloc[0]["accuracy/score"] == 0.9
        assert df.iloc[1]["accuracy/score"] == 0.8
