from collections.abc import Generator

import pytest
from returns.pipeline import is_successful

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
from luna_bench._internal.domain_models.model_metadata_domain import ModelMetadataDomain
from luna_bench._internal.domain_models.modelset_domain import ModelSetDomain
from luna_bench._internal.user_models import BenchmarkUserModel
from luna_bench.configs.config import Config
from tests.unit.fixtures.mock_components import MockAlgorithm, MockAsyncAlgorithm, MockFeature, MockMetric, MockPlot
from tests.utils.luna_model import simple_model


@pytest.fixture()
def configured_dao() -> DaoTransaction:
    sc = DaoContainer()

    cnf = Config()
    cnf.DB_CONNECTION_STRING = ":memory:"

    sc.config.from_pydantic(cnf)
    sc.reset_singletons()
    sc.wire()
    return sc.transaction()


@pytest.fixture()
def empty_transaction(configured_dao: DaoTransaction) -> Generator[DaoTransaction]:
    """Provide a transaction fixture for testing DAOs."""
    with configured_dao as t:
        try:
            yield t
        finally:
            t.rollback()


class SetupBenchmark:
    benchmark_name: str
    modelset_name: str
    model_name: str

    benchmark: BenchmarkDomain
    benchmark_usermodel: BenchmarkUserModel
    modelset: ModelSetDomain
    model_metadata: ModelMetadataDomain
    transaction: DaoTransaction


@pytest.fixture()
def setup_benchmark(empty_transaction: DaoTransaction) -> SetupBenchmark:
    """Provide a transaction fixture with a default modelset and model configured."""
    benchmark_name = "existing"
    modelset_name = "existing"
    model_name = "existing"
    algorithm_name = "existing"
    algorithm_async_name = "existing_async"
    feature_name = "existing"
    metric_name = "existing"
    plot_name = "existing"

    model = simple_model("existing")

    benchmark_result = empty_transaction.benchmark.create(benchmark_name=benchmark_name)
    assert is_successful(benchmark_result), "Benchmark creation failed for transaction_existing_benchmark"

    modelset_result = empty_transaction.modelset.create(modelset_name=modelset_name)
    assert is_successful(modelset_result), "Modelset creation failed for transaction_existing_benchmark"

    model_metadata_result = empty_transaction.model.get_or_create(
        model_name=model_name, model_hash=model.__hash__(), binary=model.encode()
    )
    assert is_successful(model_metadata_result), "Model creation failed for transaction_existing_benchmark"
    model_metadata = model_metadata_result.unwrap()

    modelset__with_model_result = empty_transaction.modelset.add_model(
        modelset_name=modelset_name, model_id=model_metadata.id
    )
    assert is_successful(modelset__with_model_result), (
        "Modelset addition of the model failed for transaction_existing_benchmark"
    )
    modelset = modelset__with_model_result.unwrap()

    empty_transaction.benchmark.set_modelset(benchmark_name=benchmark_name, modelset_name=modelset_name)

    algorithm_sync_result = empty_transaction.algorithm.add(
        benchmark_name=benchmark_name,
        algorithm_name=algorithm_name,
        registered_id=MockAlgorithm.registered_id,  # type: ignore[attr-defined] # decorator adds private field
        algorithm_type=AlgorithmType.SYNC,
        algorithm=ArbitraryDataDomain(),
    )
    assert is_successful(algorithm_sync_result), "Algorithm creation failed for transaction_existing_benchmark"

    algorithm_async_result = empty_transaction.algorithm.add(
        benchmark_name=benchmark_name,
        algorithm_name=algorithm_async_name,
        registered_id=MockAsyncAlgorithm.registered_id,  # type: ignore[attr-defined] # decorator adds private field
        algorithm_type=AlgorithmType.ASYNC,
        algorithm=ArbitraryDataDomain(),
    )
    assert is_successful(algorithm_async_result), "Algorithm creation failed for transaction_existing_benchmark"

    feature_result = empty_transaction.feature.add(
        benchmark_name=benchmark_name,
        feature_name=feature_name,
        registered_id=MockFeature.registered_id,  # type: ignore[attr-defined] # decorator adds private field
        feature_config=ArbitraryDataDomain(),
    )

    assert is_successful(feature_result), "Feature creation failed for transaction_existing_benchmark"

    metric_result = empty_transaction.metric.add(
        benchmark_name=benchmark_name,
        metric_name=metric_name,
        registered_id=MockMetric.registered_id,  # type: ignore[attr-defined] # decorator adds private field
        metric_config=ArbitraryDataDomain(),
    )

    assert is_successful(metric_result), "Metric creation failed for transaction_existing_benchmark"

    plot_result = empty_transaction.plot.add(
        benchmark_name=benchmark_name,
        plot_name=plot_name,
        registered_id=MockPlot.registered_id,  # type: ignore[attr-defined] # decorator adds private field
        plot_config=ArbitraryDataDomain(),
    )

    assert is_successful(plot_result), "Plot creation failed for transaction_existing_benchmark"

    loaded_benchmark_result = empty_transaction.benchmark.load(benchmark_name)
    assert is_successful(loaded_benchmark_result), "Benchmark loading failed for transaction_existing_benchmark"
    loaded_benchmark = loaded_benchmark_result.unwrap()

    setup_benchmark = SetupBenchmark()

    setup_benchmark.benchmark_name = benchmark_name
    setup_benchmark.modelset_name = modelset_name
    setup_benchmark.model_name = model_name
    setup_benchmark.benchmark = loaded_benchmark
    setup_benchmark.modelset = modelset
    setup_benchmark.model_metadata = model_metadata
    setup_benchmark.transaction = empty_transaction

    return setup_benchmark
