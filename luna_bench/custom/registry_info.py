from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.custom.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.custom.base_components.base_algorithm_sync import BaseAlgorithmSync
from luna_bench.custom.base_components.base_feature import BaseFeature
from luna_bench.custom.base_components.base_metric import BaseMetric
from luna_bench.custom.base_components.base_plot import BasePlot


class RegistryInfo:
    """Provides utility functions to log and retrieve information from the registries."""

    _logger = Logging.get_logger(__name__)

    @inject
    @staticmethod
    def log_registry_contents(
        feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
        algorithm_sync_registry: Registry[BaseAlgorithmSync] = Provide[RegistryContainer.algorithm_sync_registry],
        algorithm_async_registry: Registry[BaseAlgorithmAsync[BaseModel]] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
        metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
        plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
    ) -> None:
        """
        Print information about the registered features, algorithms, metrics, and plots.

        Parameters
        ----------
        feature_registry: Registry[BaseFeature], injected
        algorithm_registry: Registry[IAlgorithm[IBackend]], injected
        metric_registry: Registry[BaseMetric], injected
        plot_registry: Registry[BasePlot[Any]], injected


        """
        RegistryInfo._logger.info(f"FeatureRegistry: {feature_registry.ids()}")
        RegistryInfo._logger.info(f"BaseAlgorithmSyncRegistry: {algorithm_sync_registry.ids()}")
        RegistryInfo._logger.info(f"BaseAlgorithmAsyncRegistry: {algorithm_async_registry.ids()}")
        RegistryInfo._logger.info(f"MetricRegistry: {metric_registry.ids()}")
        RegistryInfo._logger.info(f"PlotRegistry: {plot_registry.ids()}")

    @inject
    @staticmethod
    def log_registered_features(
        feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
    ) -> list[str]:
        """
        Retrieve the feature registry.

        Parameters
        ----------
        feature_registry: Registry[BaseFeature], injected

        Returns
        -------
        Registry[BaseFeature]
            Returns the injected feature registry.

        """
        RegistryInfo._logger.info(f"FeatureRegistry: {feature_registry.ids()}")
        return feature_registry.ids()

    @inject
    @staticmethod
    def log_registered_sync(
        algorithm_registry: Registry[BaseAlgorithmSync] = Provide[RegistryContainer.algorithm_sync_registry],
    ) -> list[str]:
        """
        Retrieve the algorithm registry.

        Parameters
        ----------
        algorithm_registry: Registry[IAlgorithm[IBackend]], injected

        Returns
        -------
        Registry[IAlgorithm[IBackend]]
            Returns the injected algorithm registry.

        """
        RegistryInfo._logger.info(f"BaseAlgorithmSyncRegistry: {algorithm_registry.ids()}")
        return algorithm_registry.ids()

    @inject
    @staticmethod
    def log_registered_algorithms_async(
        algorithm_registry: Registry[BaseAlgorithmAsync[BaseModel]] = Provide[
            RegistryContainer.algorithm_async_registry
        ],
    ) -> list[str]:
        """
        Retrieve the algorithm registry.

        Parameters
        ----------
        algorithm_registry: Registry[IAlgorithm[IBackend]], injected

        Returns
        -------
        Registry[IAlgorithm[IBackend]]
            Returns the injected algorithm registry.

        """
        RegistryInfo._logger.info(f"BaseAlgorithmAsyncRegistry: {algorithm_registry.ids()}")
        return algorithm_registry.ids()

    @inject
    @staticmethod
    def log_registered_metrics(
        metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
    ) -> list[str]:
        """
        Retrieve the metric registry.

        Parameters
        ----------
        metric_registry: Registry[BaseMetric], injected

        Returns
        -------
        Registry[BaseMetric]
            Returns the injected metric registry.

        """
        RegistryInfo._logger.info(f"MetricRegistry: {metric_registry.ids()}")
        return metric_registry.ids()

    @inject
    @staticmethod
    def log_registered_plots(
        plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
    ) -> list[str]:
        """
        Retrieve the plot registry.

        Parameters
        ----------
        plot_registry: Registry[BasePlot], injected

        Returns
        -------
        Registry[BasePlot]
            Returns the injected plot registry.

        """
        RegistryInfo._logger.info(f"PlotRegistry: {plot_registry.ids()}")
        return plot_registry.ids()
