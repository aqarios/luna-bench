from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from types import TracebackType

    from pydantic import BaseModel
    from returns.result import Result

    from luna_bench._internal.domain_models import (
        AlgorithmDomain,
        AlgorithmResultDomain,
        BenchmarkDomain,
        BenchmarkStatus,
        FeatureResultDomain,
        MetricResultDomain,
        ModelMetadataDomain,
        ModelSetDomain,
        PlotDomain,
    )
    from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
    from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
    from luna_bench._internal.domain_models.feature_domain import FeatureDomain
    from luna_bench._internal.domain_models.metric_domain import MetricDomain
    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class DaoTransaction(Protocol):
    """Protocol for a database transaction."""

    def __enter__(self) -> Self: ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    @property
    def modelset(self) -> ModelSetDao: ...

    @property
    def model(self) -> ModelDao: ...

    @property
    def benchmark(self) -> BenchmarkDao: ...

    @property
    def feature(self) -> FeatureDao: ...

    @property
    def metric(self) -> MetricDao: ...

    @property
    def algorithm(self) -> AlgorithmDao: ...

    @property
    def plot(self) -> PlotDao: ...


class ModelDao(Protocol):
    """Protocol for model persistence, storing both metadata and binary model data."""

    @staticmethod
    def get(model_hash: int) -> Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError]:
        """Look up model metadata by model hash.

        Parameters
        ----------
        model_hash: int
            The hash of the model to look up.

        Returns
        -------
        Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The model metadata for the given hash.
            On failure: An error if no model with that hash exists.
        """

    @staticmethod
    def get_all() -> list[ModelMetadataDomain]:
        """Retrieve metadata for all stored models.

        Returns
        -------
        list[ModelMetadataDomain]
            A list of all model metadata domain objects.
        """

    @staticmethod
    def get_or_create(
        model_name: str, model_hash: int, binary: bytes
    ) -> Result[ModelMetadataDomain, DataNotUniqueError | UnknownLunaBenchError]:
        """Upsert model metadata by hash, inserting the binary on first creation.

        Parameters
        ----------
        model_name: str
            The display name for the model.
        model_hash: int
            The unique content hash of the model.
        binary: bytes
            The raw encoded model bytes to store if new.

        Returns
        -------
        Result[ModelMetadataDomain, UnknownLunaBenchError]
            On success: The (existing or newly created) model metadata.
            On failure: An unexpected error.
        """

    @staticmethod
    def load(model_id: int) -> Result[bytes, DataNotExistError | UnknownLunaBenchError]:
        """Load the raw binary data for a model by its id.

        Parameters
        ----------
        model_id: int
            The id of the model whose binary data to load.

        Returns
        -------
        Result[bytes, DataNotExistError | UnknownLunaBenchError]
            On success: The raw encoded model bytes.
            On failure: An error if no model with that id exists.
        """


class PlotDao(Protocol):
    """Protocol for plot config persistence."""

    @staticmethod
    def add(
        benchmark_name: str, plot_name: str, registered_id: str, plot_config: ArbitraryDataDomain
    ) -> Result[PlotDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        """Create a new plot configuration under a benchmark.

        Parameters
        ----------
        benchmark_name: str
            The name of the benchmark to attach the plot to.
        plot_name: str
            The name for the new plot.
        registered_id: str
            The registry id of the ``BasePlot`` subclass.
        plot_config: ArbitraryDataDomain
            The serialized plot configuration data.

        Returns
        -------
        Result[PlotDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]
            On success: The created plot domain object.
            On failure: An error (duplicate name, missing benchmark, or unexpected).
        """

    @staticmethod
    def remove(benchmark_name: str, plot_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete a plot configuration, cascading to related data.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the plot belongs to.
        plot_name: str
            The name of the plot to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the plot was not found.
        """

    @staticmethod
    def update(
        benchmark_name: str, plot_name: str, registered_id: str, plot_config: ArbitraryDataDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update a plot config, resetting its status to CREATED.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the plot belongs to.
        plot_name: str
            The name of the plot to update.
        registered_id: str
            The new registry id.
        plot_config: ArbitraryDataDomain
            The new serialized plot configuration.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the plot was not found.
        """

    @staticmethod
    def update_status(
        benchmark_name: str, plot_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update only the status of a plot configuration.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the plot belongs to.
        plot_name: str
            The name of the plot.
        status: BenchmarkStatus
            The new status value.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the plot was not found.
        """

    @staticmethod
    def load(benchmark_name: str, plot_name: str) -> Result[PlotDomain, DataNotExistError | UnknownLunaBenchError]:
        """Load a plot config by benchmark and plot name.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the plot belongs to.
        plot_name: str
            The name of the plot.

        Returns
        -------
        Result[PlotDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The plot domain object.
            On failure: An error if the plot was not found.
        """


class FeatureDao(Protocol):
    """Protocol for feature persistence."""

    @staticmethod
    def add(
        benchmark_name: str,
        feature_name: str,
        registered_id: str,
        feature_config: ArbitraryDataDomain,
    ) -> Result[FeatureDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        """Create a new feature under a benchmark.

        Parameters
        ----------
        benchmark_name: str
            The benchmark to attach the feature to.
        feature_name: str
            The name for the new feature.
        registered_id: str
            The registry id of the ``BaseFeature`` subclass.
        feature_config: ArbitraryDataDomain
            The serialized feature configuration.

        Returns
        -------
        Result[FeatureDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]
            On success: The created feature domain object.
            On failure: An error (duplicate name, missing benchmark, or unexpected).
        """

    @staticmethod
    def remove(benchmark_name: str, feature_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete a feature by name and benchmark.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the feature belongs to.
        feature_name: str
            The name of the feature to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the feature was not found.
        """

    @staticmethod
    def update(
        benchmark_name: str, feature_name: str, registered_id: str, feature_config: ArbitraryDataDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update a feature's config, resetting its status to CREATED.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the feature belongs to.
        feature_name: str
            The name of the feature.
        registered_id: str
            The new registry id.
        feature_config: ArbitraryDataDomain
            The new serialised feature config.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the feature was not found.
        """

    @staticmethod
    def update_status(
        benchmark_name: str, feature_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update only the status of a feature.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the feature belongs to.
        feature_name: str
            The name of the feature.
        status: BenchmarkStatus
            The new status value.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the feature was not found.
        """

    @staticmethod
    def set_result(
        benchmark_name: str, feature_name: str, result: FeatureResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Store a per-model feature result.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the feature belongs to.
        feature_name: str
            The name of the feature.
        result: FeatureResultDomain
            The result domain object containing the model id, timing, status, and data.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """

    @staticmethod
    def remove_result(
        benchmark_name: str, feature_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete all results for a feature and reset its status to CREATED.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the feature belongs to.
        feature_name: str
            The name of the feature.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """

    @staticmethod
    def load(
        benchmark_name: str, feature_name: str
    ) -> Result[FeatureDomain, DataNotExistError | UnknownLunaBenchError]:
        """Load a feature by name and benchmark, with eagerly loaded results.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the feature belongs to.
        feature_name: str
            The name of the feature.

        Returns
        -------
        Result[FeatureDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The feature domain with its results.
            On failure: An error if the feature was not found.
        """


class MetricDao(Protocol):
    """Protocol for metric persistence."""

    @staticmethod
    def add(
        benchmark_name: str, metric_name: str, registered_id: str, metric_config: ArbitraryDataDomain
    ) -> Result[MetricDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        """Create a new metric under a benchmark.

        Parameters
        ----------
        benchmark_name: str
            The benchmark to attach the metric to.
        metric_name: str
            The name for the new metric.
        registered_id: str
            The registry id of the ``BaseMetric`` subclass.
        metric_config: ArbitraryDataDomain
            The serialized metric configuration.

        Returns
        -------
        Result[MetricDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]
            On success: The created metric domain object.
            On failure: An error.
        """

    @staticmethod
    def remove(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete a metric by name and benchmark.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the metric belongs to.
        metric_name: str
            The name of the metric to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the metric was not found.
        """

    @staticmethod
    def update(
        benchmark_name: str, metric_name: str, registered_id: str, metric_config: BaseModel
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update a metric's config, resetting its status to CREATED.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the metric belongs to.
        metric_name: str
            The name of the metric.
        registered_id: str
            The new registry id.
        metric_config: BaseModel
            The new serialised metric config.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the metric was not found.
        """

    @staticmethod
    def update_status(
        benchmark_name: str, metric_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update only the status of a metric.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the metric belongs to.
        metric_name: str
            The name of the metric.
        status: BenchmarkStatus
            The new status value.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the metric was not found.
        """

    @staticmethod
    def set_result(
        benchmark_name: str, metric_name: str, result: MetricResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Store a per-model-per-algorithm metric result.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the metric belongs to.
        metric_name: str
            The name of the metric.
        result: MetricResultDomain
            The result domain object including algorithm, model, timing, and data.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """

    @staticmethod
    def remove_result(benchmark_name: str, metric_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete all results for a metric and reset its status to CREATED.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the metric belongs to.
        metric_name: str
            The name of the metric.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """

    @staticmethod
    def load(benchmark_name: str, metric_name: str) -> Result[MetricDomain, DataNotExistError | UnknownLunaBenchError]:
        """Load a metric by name and benchmark, with eagerly loaded results.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the metric belongs to.
        metric_name: str
            The name of the metric.

        Returns
        -------
        Result[MetricDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The metric domain with its results.
            On failure: An error if the metric was not found.
        """


class AlgorithmDao(Protocol):
    """Protocol for algorithm persistence."""

    @staticmethod
    def add(
        benchmark_name: str,
        algorithm_name: str,
        registered_id: str,
        algorithm_type: AlgorithmType,
        algorithm: ArbitraryDataDomain,
    ) -> Result[AlgorithmDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]:
        """Create a new algorithm under a benchmark.

        Parameters
        ----------
        benchmark_name: str
            The benchmark to attach the algorithm to.
        algorithm_name: str
            The name for the new algorithm.
        registered_id: str
            The registry id of the ``BaseAlgorithmAsync`` / ``BaseAlgorithmSync`` subclass.
        algorithm_type: AlgorithmType
            Whether this is a ``SYNC`` or ``ASYNC`` algorithm.
        algorithm: ArbitraryDataDomain
            The serialized algorithm configuration.

        Returns
        -------
        Result[AlgorithmDomain, DataNotUniqueError | DataNotExistError | UnknownLunaBenchError]
            On success: The created algorithm domain object.
            On failure: An error.
        """

    @staticmethod
    def remove(benchmark_name: str, algorithm_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete an algorithm by name and benchmark.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the algorithm belongs to.
        algorithm_name: str
            The name of the algorithm to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the algorithm was not found.
        """

    @staticmethod
    def update(
        benchmark_name: str,
        algorithm_name: str,
        registered_id: str,
        algorithm_config: ArbitraryDataDomain,
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update an algorithm's config, resetting its status to CREATED.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the algorithm belongs to.
        algorithm_name: str
            The name of the algorithm.
        registered_id: str
            The new registry id.
        algorithm_config: ArbitraryDataDomain
            The new serialised algorithm config.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the algorithm was not found.
        """

    @staticmethod
    def update_status(
        benchmark_name: str, algorithm_name: str, status: BenchmarkStatus
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Update only the status of an algorithm.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the algorithm belongs to.
        algorithm_name: str
            The name of the algorithm.
        status: BenchmarkStatus
            The new status value.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the algorithm was not found.
        """

    @staticmethod
    def load(
        benchmark_name: str, algorithm_name: str
    ) -> Result[AlgorithmDomain, DataNotExistError | UnknownLunaBenchError]:
        """Load an algorithm by name and benchmark, with eagerly loaded results.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the algorithm belongs to.
        algorithm_name: str
            The name of the algorithm.

        Returns
        -------
        Result[AlgorithmDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The algorithm domain with its results.
            On failure: An error if the algorithm was not found.
        """

    @staticmethod
    def set_result(
        benchmark_name: str, algorithm_name: str, result: AlgorithmResultDomain
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Store a per-model algorithm result (upsert semantics).

        Parameters
        ----------
        benchmark_name: str
            The benchmark the algorithm belongs to.
        algorithm_name: str
            The name of the algorithm.
        result: AlgorithmResultDomain
            The result domain object including model, solution, status, and task id.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """

    @staticmethod
    def remove_result(
        benchmark_name: str, algorithm_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete all results for an algorithm.

        Parameters
        ----------
        benchmark_name: str
            The benchmark the algorithm belongs to.
        algorithm_name: str
            The name of the algorithm.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """


class BenchmarkDao(Protocol):
    """Protocol for benchmark persistence."""

    @staticmethod
    def create(benchmark_name: str) -> Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]:
        """Create a new benchmark with CREATED status and no modelset.

        Parameters
        ----------
        benchmark_name: str
            The unique name for the new benchmark.

        Returns
        -------
        Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError]
            On success: The created benchmark domain object.
            On failure: An error if a benchmark with that name already exists.
        """

    @staticmethod
    def load(benchmark_name: str) -> Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]:
        """Load a benchmark by name, eagerly loading its child components.

        Parameters
        ----------
        benchmark_name: str
            The name of the benchmark to load.

        Returns
        -------
        Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The benchmark domain with all child components loaded.
            On failure: An error if the benchmark was not found.
        """

    @staticmethod
    def delete(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete a benchmark by name.

        Parameters
        ----------
        benchmark_name: str
            The name of the benchmark to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the benchmark was not found.
        """

    @staticmethod
    def load_all() -> Result[list[BenchmarkDomain], UnknownLunaBenchError]:
        """Load all benchmarks.

        Returns
        -------
        Result[list[BenchmarkDomain], UnknownLunaBenchError]
            On success: A list of all benchmark domain objects.
            On failure: An unexpected error.
        """

    @staticmethod
    def set_modelset(
        benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Assign a model set to a benchmark.

        Parameters
        ----------
        benchmark_name: str
            The name of the benchmark.
        modelset_name: str
            The name of the model set to assign.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error.
        """

    @staticmethod
    def remove_modelset(benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Remove the model set assignment from a benchmark.

        Parameters
        ----------
        benchmark_name: str
            The name of the benchmark.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the benchmark was not found.
        """


class ModelSetDao(Protocol):
    """Protocol for model set persistence."""

    @staticmethod
    def create(modelset_name: str) -> Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]:
        """Create a new model set.

        Parameters
        ----------
        modelset_name: str
            The unique name for the model set.

        Returns
        -------
        Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError]
            On success: The created model set domain object.
            On failure: An error if a model set with that name already exists.
        """

    @staticmethod
    def load(modelset_name: str) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        """Load a model set by name.

        Parameters
        ----------
        modelset_name: str
            The name of the model set.

        Returns
        -------
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The model set domain object.
            On failure: An error if the model set was not found.
        """

    @staticmethod
    def delete(modelset_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Delete a model set, cascade-removing orphaned model metadata.

        Removes the M2M associations and then garbage-collects any ``ModelMetadata``
        rows that are no longer referenced by any model set.

        Parameters
        ----------
        modelset_name: str
            The name of the model set to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing.
            On failure: An error if the model set was not found.
        """

    @staticmethod
    def add_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        """Associate a model with a model set via the M2M relationship.

        Parameters
        ----------
        modelset_name: str
            The name of the model set.
        model_id: int
            The id of the model to add.

        Returns
        -------
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The updated model set domain object.
            On failure: An error.
        """

    @staticmethod
    def remove_model(
        modelset_name: str, model_id: int
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        """Disassociate a model from a model set, garbage-collecting orphaned metadata.

        Removes the M2M association. If the model is no longer in any model set,
        cascade-deletes its metadata row.

        Parameters
        ----------
        modelset_name: str
            The name of the model set.
        model_id: int
            The id of the model to remove.

        Returns
        -------
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: The updated model set domain object.
            On failure: An error.
        """

    @staticmethod
    def load_all() -> Result[list[ModelSetDomain], UnknownLunaBenchError]:
        """Load all model sets.

        Returns
        -------
        Result[list[ModelSetDomain], UnknownLunaBenchError]
            On success: A list of all model set domain objects.
            On failure: An unexpected error.
        """

    @staticmethod
    def load_all_models(
        modelset_name: str,
    ) -> Result[list[ModelMetadataDomain], DataNotExistError | UnknownLunaBenchError]:
        """Load all models within a model set, using an eager-loaded backref.

        Parameters
        ----------
        modelset_name: str
            The name of the model set.

        Returns
        -------
        Result[list[ModelMetadataDomain], DataNotExistError | UnknownLunaBenchError]
            On success: A list of model metadata for all models in the set.
            On failure: An error if the model set was not found.
        """
