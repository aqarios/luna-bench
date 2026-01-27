from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from luna_bench import _registry_container
from luna_bench.helpers.decorators import (
    algorithms_async,
    algorithms_sync,
    features,
    metrics,
    plots,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

    from luna_bench._internal.registries.protocols import Registry
    from luna_bench.base_components import (
        BaseAlgorithmAsync,
        BaseAlgorithmSync,
        BaseFeature,
        BaseMetric,
        BasePlot,
    )


class TestDecoratorsRegistryInjection:
    def test_features_registry_injection(self) -> None:
        """Verify that the feature registry is correctly injected and returned."""
        mock_registry: MagicMock = MagicMock()
        with _registry_container.feature_registry.override(mock_registry):
            registry: Registry[BaseFeature] = features()
            assert registry is mock_registry

    def test_algorithms_sync_registry_injection(self) -> None:
        """Verify that the synchronous algorithm registry is correctly injected and returned."""
        mock_registry: MagicMock = MagicMock()
        with _registry_container.algorithm_sync_registry.override(mock_registry):
            registry: Registry[BaseAlgorithmSync] = algorithms_sync()
            assert registry is mock_registry

    def test_algorithms_async_registry_injection(self) -> None:
        """Verify that the asynchronous algorithm registry is correctly injected and returned."""
        mock_registry: MagicMock = MagicMock()
        with _registry_container.algorithm_async_registry.override(mock_registry):
            registry: Registry[BaseAlgorithmAsync[BaseModel]] = algorithms_async()
            assert registry is mock_registry

    def test_metrics_registry_injection(self) -> None:
        """Verify that the metric registry is correctly injected and returned."""
        mock_registry: MagicMock = MagicMock()
        with _registry_container.metric_registry.override(mock_registry):
            registry: Registry[BaseMetric] = metrics()
            assert registry is mock_registry

    def test_plots_registry_injection(self) -> None:
        """Verify that the plot registry is correctly injected and returned."""
        mock_registry: MagicMock = MagicMock()
        with _registry_container.plot_registry.override(mock_registry):
            registry: Registry[BasePlot[Any]] = plots()
            assert registry is mock_registry
