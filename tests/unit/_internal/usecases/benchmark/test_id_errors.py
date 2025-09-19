from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result

from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench._internal.usecases.benchmark import AlgorithmAddUcImpl, FeatureAddUcImpl, MetricAddUcImpl
from luna_bench._internal.usecases.benchmark.plot.plot_add import PlotAddUcImpl
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric, MockPlot

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction
    from luna_bench._internal.domain_models import RegisteredDataDomain


class TestIdErrors:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(configured_dao: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        configured_dao.benchmark.create(benchmark_name="existing")

        return configured_dao

    class DummyRegistry(ArbitraryDataRegistry[Any]):
        def get_by_id(self, registered_id: str) -> Result[type[RegisteredDataDomain], UnknownIdError]:
            return Failure(UnknownIdError("Dummy", registered_id))

    def test_add_id_error(self, setup_transaction: DaoTransaction) -> None:
        registry = TestIdErrors.DummyRegistry("Dummy")

        registry.register("algorithm", MockAlgorithm)
        registry.register("feature", MockFeature)
        registry.register("metric", MockMetric)
        registry.register("plot", MockPlot)

        result_algorithm = AlgorithmAddUcImpl(transaction=setup_transaction, registry=registry)(
            "existing", "non-existing", MockAlgorithm()
        )
        result_feature = FeatureAddUcImpl(transaction=setup_transaction, registry=registry)(
            "existing", "non-existing", MockFeature()
        )
        result_metric = MetricAddUcImpl(transaction=setup_transaction, registry=registry)(
            "existing", "non-existing", MockMetric()
        )
        result_plot = PlotAddUcImpl(transaction=setup_transaction, registry=registry)(
            "existing", "non-existing", MockPlot()
        )

        assert not is_successful(result_algorithm)
        assert not is_successful(result_feature)
        assert not is_successful(result_metric)
        assert not is_successful(result_plot)

        assert isinstance(result_algorithm.failure(), UnknownIdError)
        assert isinstance(result_feature.failure(), UnknownIdError)
        assert isinstance(result_metric.failure(), UnknownIdError)
        assert isinstance(result_plot.failure(), UnknownIdError)
