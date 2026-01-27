from collections.abc import Generator
from contextlib import ExitStack
from unittest.mock import MagicMock

import pytest
from returns.result import Failure, Success

from luna_bench.components.benchmark import Benchmark
from luna_bench.components.model_set import ModelSet
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    ErrorHandlingMode,
    FeatureEntity,
    JobStatus,
    MetricEntity,
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
