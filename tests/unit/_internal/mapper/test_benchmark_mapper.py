from unittest.mock import MagicMock

import pytest
from returns.result import Failure, Success

from luna_bench._internal.domain_models import (
    BenchmarkDomain,
    BenchmarkStatus,
    ModelMetadataDomain,
    ModelSetDomain,
)
from luna_bench._internal.mappers.benchmark_mapper import BenchmarkMapper
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class TestBenchmarkMapper:
    @pytest.fixture()
    def mock_feature_mapper(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture()
    def mock_metric_mapper(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture()
    def mock_algorithm_mapper(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture()
    def mock_plot_mapper(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture()
    def benchmark_mapper(
        self,
        mock_feature_mapper: MagicMock,
        mock_metric_mapper: MagicMock,
        mock_algorithm_mapper: MagicMock,
        mock_plot_mapper: MagicMock,
    ) -> BenchmarkMapper:
        return BenchmarkMapper(
            feature_mapper=mock_feature_mapper,
            metric_mapper=mock_metric_mapper,
            algorithm_mapper=mock_algorithm_mapper,
            plot_mapper=mock_plot_mapper,
        )

    def test_to_user_model_feature_failure(
        self, benchmark_mapper: BenchmarkMapper, mock_feature_mapper: MagicMock
    ) -> None:
        domain = BenchmarkDomain.model_construct(
            name="test",
            status=BenchmarkStatus.CREATED,
            modelset=None,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[],
        )
        error = UnknownIdError("feature", "1")
        mock_feature_mapper.to_user_model_list.return_value = Failure(error)

        result = benchmark_mapper.to_user_model(domain)

        assert isinstance(result, Failure)
        assert result.failure() == error

    def test_to_user_model_metric_failure(
        self,
        benchmark_mapper: BenchmarkMapper,
        mock_feature_mapper: MagicMock,
        mock_metric_mapper: MagicMock,
    ) -> None:
        domain = BenchmarkDomain.model_construct(
            name="test",
            status=BenchmarkStatus.CREATED,
            modelset=None,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[],
        )
        mock_feature_mapper.to_user_model_list.return_value = Success([])
        error = UnknownIdError("metric", "1")
        mock_metric_mapper.to_user_model_list.return_value = Failure(error)

        result = benchmark_mapper.to_user_model(domain)

        assert isinstance(result, Failure)
        assert result.failure() == error

    def test_to_user_model_algorithm_failure(
        self,
        benchmark_mapper: BenchmarkMapper,
        mock_feature_mapper: MagicMock,
        mock_metric_mapper: MagicMock,
        mock_algorithm_mapper: MagicMock,
    ) -> None:
        domain = BenchmarkDomain.model_construct(
            name="test",
            status=BenchmarkStatus.CREATED,
            modelset=None,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[],
        )
        mock_feature_mapper.to_user_model_list.return_value = Success([])
        mock_metric_mapper.to_user_model_list.return_value = Success([])
        error = UnknownIdError("algorithm", "1")
        mock_algorithm_mapper.to_user_model_list.return_value = Failure(error)

        result = benchmark_mapper.to_user_model(domain)

        assert isinstance(result, Failure)
        assert result.failure() == error

    def test_to_user_model_plot_failure(
        self,
        benchmark_mapper: BenchmarkMapper,
        mock_feature_mapper: MagicMock,
        mock_metric_mapper: MagicMock,
        mock_algorithm_mapper: MagicMock,
        mock_plot_mapper: MagicMock,
    ) -> None:
        domain = BenchmarkDomain.model_construct(
            name="test",
            status=BenchmarkStatus.CREATED,
            modelset=None,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[],
        )
        mock_feature_mapper.to_user_model_list.return_value = Success([])
        mock_metric_mapper.to_user_model_list.return_value = Success([])
        mock_algorithm_mapper.to_user_model_list.return_value = Success([])
        error = UnknownIdError("plot", "1")
        mock_plot_mapper.to_user_model_list.return_value = Failure(error)

        result = benchmark_mapper.to_user_model(domain)

        assert isinstance(result, Failure)
        assert result.failure() == error

    def test_to_user_model_success_with_modelset(
        self,
        benchmark_mapper: BenchmarkMapper,
        mock_feature_mapper: MagicMock,
        mock_metric_mapper: MagicMock,
        mock_algorithm_mapper: MagicMock,
        mock_plot_mapper: MagicMock,
    ) -> None:
        model_domain = ModelMetadataDomain(id=1, name="model1", hash=123)
        modelset_domain = ModelSetDomain(id=1, name="set1", models=[model_domain])
        domain = BenchmarkDomain.model_construct(
            name="test",
            status=BenchmarkStatus.CREATED,
            modelset=modelset_domain,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[],
        )

        mock_feature_mapper.to_user_model_list.return_value = Success(["f1"])
        mock_metric_mapper.to_user_model_list.return_value = Success(["m1"])
        mock_algorithm_mapper.to_user_model_list.return_value = Success(["a1"])
        mock_plot_mapper.to_user_model_list.return_value = Success(["p1"])

        result = benchmark_mapper.to_user_model(domain)

        assert isinstance(result, Success)
        entity = result.unwrap()
        assert entity.name == "test"
        assert entity.features == ["f1"]
        assert entity.metrics == ["m1"]
        assert entity.algorithms == ["a1"]
        assert entity.plots == ["p1"]
        assert entity.modelset is not None
        assert entity.modelset.id == 1
        assert entity.modelset.name == "set1"
        assert len(entity.modelset.models) == 1
        assert entity.modelset.models[0].id == 1
        assert entity.modelset.models[0].name == "model1"
        assert entity.modelset.models[0].hash == 123

    def test_to_user_model_success_without_modelset(
        self,
        benchmark_mapper: BenchmarkMapper,
        mock_feature_mapper: MagicMock,
        mock_metric_mapper: MagicMock,
        mock_algorithm_mapper: MagicMock,
        mock_plot_mapper: MagicMock,
    ) -> None:
        domain = BenchmarkDomain.model_construct(
            name="test",
            status=BenchmarkStatus.CREATED,
            modelset=None,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[],
        )

        mock_feature_mapper.to_user_model_list.return_value = Success([])
        mock_metric_mapper.to_user_model_list.return_value = Success([])
        mock_algorithm_mapper.to_user_model_list.return_value = Success([])
        mock_plot_mapper.to_user_model_list.return_value = Success([])

        result = benchmark_mapper.to_user_model(domain)

        assert isinstance(result, Success)
        entity = result.unwrap()
        assert entity.name == "test"
        assert entity.modelset is None
