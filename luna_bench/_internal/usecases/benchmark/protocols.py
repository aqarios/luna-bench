from typing import Any, Protocol

from luna_model import Solution
from pydantic import BaseModel, ValidationError
from returns.maybe import Maybe
from returns.result import Result

from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench.custom import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    MetricEntity,
    ModelMetadataEntity,
    PlotEntity,
)
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.run_errors.run_plot_missing_error import RunPlotMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BenchmarkCreateUc(Protocol):
    """Protocol for creating a new benchmark."""

    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkEntity, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError]:
        """Open a DAO transaction, create a benchmark, and map the domain to an entity.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark to create.

        Returns
        -------
        Result[BenchmarkEntity, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError]
            The newly created benchmark entity on success, or an error if the
            name already exists, a registry ID is unknown, validation fails, or
            an unexpected error occurs.
        """


class BenchmarkDeleteUc(Protocol):
    """Protocol for deleting a benchmark."""

    def __call__(self, benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and delete the benchmark by name.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the benchmark does not exist or an
            unexpected error occurs.
        """


class BenchmarkLoadUc(Protocol):
    """Protocol for loading a single benchmark."""

    def __call__(
        self, benchmark_name: str
    ) -> Result[BenchmarkEntity, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError]:
        """Open a DAO transaction, load a benchmark, and map the domain to an entity.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark to load.

        Returns
        -------
        Result[BenchmarkEntity, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError]
            The benchmark entity on success, or an error if it does not exist,
            a registry ID is unknown, validation fails, or an unexpected error occurs.
        """


class BenchmarkLoadAllUc(Protocol):
    """Protocol for loading all benchmarks."""

    def __call__(
        self,
    ) -> Result[list[BenchmarkEntity], UnknownLunaBenchError | UnknownIdError | ValidationError]:
        """Open a DAO transaction, load all benchmarks, and map each domain to an entity.

        Returns
        -------
        Result[list[BenchmarkEntity], UnknownLunaBenchError | UnknownIdError | ValidationError]
            A list of all benchmark entities on success, or an error if a registry
            ID is unknown, validation fails, or an unexpected error occurs.
        """


class MetricAddUc(Protocol):
    """Protocol for adding a metric to a benchmark."""

    def __call__(
        self, benchmark_name: str, name: str, metric: BaseMetric
    ) -> Result[
        MetricEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        """Convert the metric to a registered data domain via the registry, then persist it.

        Parameters
        ----------
        benchmark_name: str
            Name of the target benchmark.
        name: str
            Name to assign to the metric.
        metric: BaseMetric
            The metric instance to register and persist.

        Returns
        -------
        Result[
            MetricEntity,
            DataNotUniqueError | DataNotExistError | UnknownLunaBenchError
            | UnknownComponentError | UnknownIdError | ValidationError,
        ]
            The metric entity on success, or an error if the component is unknown,
            the name is not unique, the benchmark does not exist, a registry ID is
            unknown, validation fails, or an unexpected error occurs.
        """


class MetricRunUc(Protocol):
    """Protocol for running metrics on a benchmark."""

    def __call__(
        self, benchmark: BenchmarkEntity, metric: MetricEntity | None = None
    ) -> Result[None, RunMetricMissingError | RunModelsetMissingError | RunFeatureMissingError]:
        """Iterate over all (algorithm, model, metric) combos, run the metric, and persist results.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose algorithm-model results to evaluate.
        metric: MetricEntity | None
            Specific metric to run, or None to run all metrics.

        Returns
        -------
        Result[None, RunMetricMissingError | RunModelsetMissingError | RunFeatureMissingError]
            None on success, or an error if no metric is found, the modelset is
            missing, or a required feature result is missing.
        """


class FeatureAddUc(Protocol):
    """Protocol for adding a feature to a benchmark."""

    def __call__(
        self, benchmark_name: str, name: str, feature: BaseFeature
    ) -> Result[
        FeatureEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        """Convert the feature to a registered data domain via the registry, then persist it.

        Parameters
        ----------
        benchmark_name: str
            Name of the target benchmark.
        name: str
            Name to assign to the feature.
        feature: BaseFeature
            The feature instance to register and persist.

        Returns
        -------
        Result[
            FeatureEntity,
            DataNotUniqueError | DataNotExistError | UnknownLunaBenchError
            | UnknownComponentError | UnknownIdError | ValidationError,
        ]
            The feature entity on success, or an error if the component is unknown,
            the name is not unique, the benchmark does not exist, a registry ID is
            unknown, validation fails, or an unexpected error occurs.
        """
        ...


class FeatureRunUc(Protocol):
    """Protocol for running features on a benchmark."""

    def __call__(
        self, benchmark: BenchmarkEntity, feature: FeatureEntity | None = None
    ) -> Result[None, RunFeatureMissingError | RunModelsetMissingError]:
        """Load and decode each model, call ``feature.run(model)``, and persist results.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose models to process.
        feature: FeatureEntity | None
            Specific feature to run, or None to run all features.

        Returns
        -------
        Result[None, RunFeatureMissingError | RunModelsetMissingError]
            None on success, or an error if no feature is found or the modelset
            is missing.
        """


class PlotAddUc(Protocol):
    """Protocol for adding a plot to a benchmark."""

    def __call__(
        self, benchmark_name: str, name: str, plot: BasePlot
    ) -> Result[
        PlotEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        """Convert the plot to a registered data domain via the registry, then persist it.

        Parameters
        ----------
        benchmark_name: str
            Name of the target benchmark.
        name: str
            Name to assign to the plot.
        plot: BasePlot
            The plot instance to register and persist.

        Returns
        -------
        Result[
            PlotEntity,
            DataNotUniqueError | DataNotExistError | UnknownLunaBenchError
            | UnknownComponentError | UnknownIdError | ValidationError,
        ]
            The plot entity on success, or an error if the component is unknown,
            the name is not unique, the benchmark does not exist, a registry ID is
            unknown, validation fails, or an unexpected error occurs.
        """


class AlgorithmAddUc(Protocol):
    """Protocol for adding an algorithm to a benchmark."""

    def __call__(
        self, benchmark_name: str, name: str, algorithm: BaseAlgorithmSync | BaseAlgorithmAsync[Any]
    ) -> Result[
        AlgorithmEntity,
        DataNotUniqueError
        | DataNotExistError
        | UnknownLunaBenchError
        | UnknownComponentError
        | UnknownIdError
        | ValidationError,
    ]:
        """Convert the algorithm to a registered data domain via the registry, then persist it.

        Handles both sync and async algorithms via isinstance checks and persists
        with the appropriate ``AlgorithmType``.

        Parameters
        ----------
        benchmark_name: str
            Name of the target benchmark.
        name: str
            Name to assign to the algorithm.
        algorithm: BaseAlgorithmSync | BaseAlgorithmAsync[Any]
            The algorithm instance to register and persist.

        Returns
        -------
        Result[
            AlgorithmEntity,
            DataNotUniqueError | DataNotExistError | UnknownLunaBenchError
            | UnknownComponentError | UnknownIdError | ValidationError,
        ]
            The algorithm entity on success, or an error if the component is unknown,
            the name is not unique, the benchmark does not exist, a registry ID is
            unknown, validation fails, or an unexpected error occurs.
        """


class AlgorithmRunUc(Protocol):
    """Protocol for running algorithms on a benchmark."""

    def __call__(
        self, benchmark: BenchmarkEntity, algorithm: AlgorithmEntity | None = None
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError]:
        """Orchestrate the full algorithm run pipeline: dispatch sync/async, poll results.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose algorithms to run.
        algorithm: AlgorithmEntity | None
            Specific algorithm to run, or None to run all algorithms.

        Returns
        -------
        Result[None, RunAlgorithmMissingError | RunModelsetMissingError]
            None on success, or an error if no algorithm is found or the modelset
            is missing.
        """


class AlgorithmFilterUc(Protocol):
    """Protocol for filtering algorithms by sync/async type."""

    def __call__(
        self, benchmark: BenchmarkEntity, algorithm_type: AlgorithmType, algorithm: AlgorithmEntity | None = None
    ) -> Result[list[AlgorithmEntity], RunAlgorithmMissingError]:
        """Filter algorithms in the benchmark by sync/async type using isinstance checks.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark containing the algorithms.
        algorithm_type: AlgorithmType
            The type to filter by (sync or async).
        algorithm: AlgorithmEntity | None
            Specific algorithm to filter, or None to filter all.

        Returns
        -------
        Result[list[AlgorithmEntity], RunAlgorithmMissingError]
            A list of matching algorithm entities on success, or an error if no
            algorithm is found.
        """


class AlgorithmRunAsBackgroundTasksUc(Protocol):
    """Protocol for launching algorithms as background tasks."""

    def __call__(
        self,
        benchmark_name: str,
        models: list[ModelMetadataEntity],
        algorithms: list[AlgorithmEntity],
    ) -> None:
        """Iterate over the product of algorithms and models, skip DONE pairs, and delegate execution.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark being run.
        models: list[ModelMetadataEntity]
            List of models to pair with algorithms.
        algorithms: list[AlgorithmEntity]
            List of algorithms to run.
        """


class AlgorithmRetrieveAsyncRetrivalDataUc(Protocol):
    """Protocol for retrieving async retrieval data from background tasks."""

    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        """Poll async background tasks and store retrieval data on success.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose async tasks to poll.

        Returns
        -------
        Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
            None on success, or an error if model decoding fails, data is missing,
            a runtime error occurs, or an unexpected error occurs.
        """


class AlgorithmRetrieveAsyncSolutionsUc(Protocol):
    """Protocol for retrieving async algorithm solutions."""

    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError]:
        """For each RUNNING async result, load the model and call ``algorithm.fetch_result(model, retrival_data)``.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose async solutions are to retrieve.

        Returns
        -------
        Result[None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if algorithms are missing, the modelset
            is missing, data does not exist, or an unexpected error occurs.
        """


class AlgorithmRetrieveSyncSolutionsUc(Protocol):
    """Protocol for retrieving sync algorithm solutions."""

    def __call__(
        self, benchmark: BenchmarkEntity
    ) -> Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]:
        """Poll sync background tasks, collect RUNNING results, and store solutions.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose sync solutions to retrieve.

        Returns
        -------
        Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
            None on success, or an error if model decoding fails, data is missing,
            a runtime error occurs, or an unexpected error occurs.
        """


class MetricRemoveUc(Protocol):
    """Protocol for removing a metric from a benchmark."""

    def __call__(
        self, benchmark_name: str, metric_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and remove the metric by name.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark containing the metric.
        metric_name: str
            Name of the metric to remove.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the metric does not exist or an
            unexpected error occurs.
        """


class FeatureRemoveUc(Protocol):
    """Protocol for removing a feature from a benchmark."""

    def __call__(
        self, benchmark_name: str, feature_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and remove the feature by name.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark containing the feature.
        feature_name: str
            Name of the feature to remove.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the feature does not exist or an
            unexpected error occurs.
        """


class BenchmarkRemoveModelsetUc(Protocol):
    """Protocol for removing a modelset from a benchmark."""

    def __call__(self, benchmark_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and remove the modelset from the benchmark.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark whose modelset to remove.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the benchmark does not exist or an
            unexpected error occurs.
        """


class PlotRemoveUc(Protocol):
    """Protocol for removing a plot from a benchmark."""

    def __call__(self, benchmark_name: str, plot_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and remove the plot by name.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark containing the plot.
        plot_name: str
            Name of the plot to remove.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the plot does not exist or an
            unexpected error occurs.
        """


class AlgorithmRemoveUc(Protocol):
    """Protocol for removing an algorithm from a benchmark."""

    def __call__(
        self, benchmark_name: str, solvejob_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and remove the algorithm by name.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark containing the algorithm.
        solvejob_name: str
            Name of the algorithm/solvejob to remove.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the algorithm does not exist or an
            unexpected error occurs.
        """


class BenchmarkSetModelsetUc(Protocol):
    """Protocol for setting the modelset on a benchmark."""

    def __call__(
        self, benchmark_name: str, modelset_name: str
    ) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """Open a DAO transaction and set the modelset on the benchmark.

        Parameters
        ----------
        benchmark_name: str
            Name of the benchmark to update.
        modelset_name: str
            Name of the modelset to assign.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            None on success, or an error if the benchmark does not exist or an
            unexpected error occurs.
        """


class PlotsRunUc(Protocol):
    """Protocol for running plots on a benchmark."""

    def __call__(
        self,
        benchmark: BenchmarkEntity,
        plot: PlotEntity | None = None,
    ) -> Result[
        None,
        RunFeatureMissingError | RunPlotMissingError | PlotRunError | UnknownLunaBenchError | RunMetricMissingError,
    ]:
        """For each plot, build result containers and call ``plot.run(result)``.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose results to visualize.
        plot: PlotEntity | None
            Specific plot to run, or None to run all plots.

        Returns
        -------
        Result[
            None,
            RunFeatureMissingError | RunPlotMissingError | PlotRunError
            | UnknownLunaBenchError | RunMetricMissingError,
        ]
            None on success, or an error if features, metrics, or plots are
            missing, a plot runtime error occurs, or an unexpected error occurs.
        """


class BackgroundRunAlgorithmAsyncUc(Protocol):
    """Protocol for running an async algorithm in the background."""

    def __call__(self, algorithm: BaseAlgorithmAsync[Any], model_id: int) -> str:
        """Delegate to ``BackgroundAlgorithmRunner.run_async()`` and return the task ID.

        Parameters
        ----------
        algorithm: BaseAlgorithmAsync[Any]
            The async algorithm to run.
        model_id: int
            Identifier of the model to run against.

        Returns
        -------
        str
            The task ID string for tracking the background job.
        """


class BackgroundRunAlgorithmSyncUc(Protocol):
    """Protocol for running a sync algorithm in the background."""

    def __call__(self, algorithm: BaseAlgorithmSync, model_id: int) -> str:
        """Delegate to ``BackgroundAlgorithmRunner.run_sync()`` and return the task ID.

        Parameters
        ----------
        algorithm: BaseAlgorithmSync
            The sync algorithm to run.
        model_id: int
            Identifier of the model to run against.

        Returns
        -------
        str
            The task ID string for tracking the background job.
        """


class BackgroundRetrieveAlgorithmAsyncUc(Protocol):
    """Protocol for retrieving results from an async background algorithm."""

    def __call__(
        self, task_id: str
    ) -> Maybe[
        Result[BaseModel, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]:
        """Delegate to ``BackgroundAlgorithmRunner.retrieve_task_result()`` and wrap in ``Maybe``.

        Parameters
        ----------
        task_id: str
            The task ID of the background job to poll.

        Returns
        -------
        Maybe[
            Result[
                BaseModel,
                ModelDecodingError | DataNotExistError | UnknownLunaBenchError
                | RunAlgorithmRuntimeError,
            ]
        ]
            A ``Maybe`` containing the result on completion, or ``Nothing`` if
            the task is still running. The inner ``Result`` holds either the
            returned ``BaseModel`` or an error.
        """


class BackgroundRetrieveAlgorithmSyncUc(Protocol):
    """Protocol for retrieving results from a sync background algorithm."""

    def __call__(
        self, task_id: str
    ) -> Maybe[
        Result[Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError]
    ]:
        """Poll a sync background task for its result, expected to be a ``Solution``.

        Parameters
        ----------
        task_id: str
            The task ID of the background job to poll.

        Returns
        -------
        Maybe[
            Result[
                Solution,
                ModelDecodingError | DataNotExistError | UnknownLunaBenchError
                | RunAlgorithmRuntimeError,
            ]
        ]
            A ``Maybe`` containing the solution on completion, or ``Nothing`` if
            the task is still running. The inner ``Result`` holds either the
            ``Solution`` or an error.
        """


class DataDirSetupUc(Protocol):
    """Protocol for setting up the data directory for a benchmark run."""

    def __call__(
        self,
        benchmark: BenchmarkEntity,
        root_folder: str | None = None,
    ) -> Result[None, str]:
        """Create the data directory structure needed for a benchmark run.

        Parameters
        ----------
        benchmark: BenchmarkEntity
            The benchmark whose data directory to set up.
        root_folder: str | None
            Optional root folder path. If None, a default location is used.

        Returns
        -------
        Result[None, str]
            None on success, or a string error message if the directory
            could not be created.
        """
