from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

import pandas as pd
from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from pydantic import BaseModel, TypeAdapter, ValidationError
from returns.pipeline import is_successful

from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmAddUc,
    AlgorithmRemoveUc,
    AlgorithmRunUc,
    BenchmarkCreateUc,
    BenchmarkLoadAllUc,
    BenchmarkLoadUc,
    BenchmarkRemoveModelsetUc,
    BenchmarkSetModelsetUc,
    FeatureAddUc,
    FeatureRemoveUc,
    FeatureRunUc,
    MetricAddUc,
    MetricRemoveUc,
    MetricRunUc,
    PlotAddUc,
    PlotRemoveUc,
    PlotsRunUc,
)
from luna_bench._internal.usecases.modelset.protocols import ModelSetLoadUc
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench._internal.wrappers import LunaAlgorithmWrapper
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.components.model_set import ModelSet
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    FeatureEntity,
    MetricEntity,
    PlotEntity,
)
from luna_bench.entities.enums import ErrorHandlingMode
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

    from returns.result import Result

ResultEntityT = TypeVar("ResultEntityT", MetricEntity, FeatureEntity)


class Benchmark(BenchmarkEntity):
    """
    Benchmark class represents a benchmark in the LunaBench system.

    This class is responsible for managing benchmark-related operations, including creating and deleting benchmarks.
    It provides methods for interacting with the benchmark data and executing benchmark runs.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    @staticmethod
    @inject
    def __run_plots_uc(
        benchmark_run_plots: PlotsRunUc = Provide[UsecaseContainer.benchmark_run_plots_uc],
    ) -> PlotsRunUc:
        return benchmark_run_plots

    @staticmethod
    @inject
    def __run_feature_uc(
        benchmark_run_features: FeatureRunUc = Provide[UsecaseContainer.benchmark_run_feature_uc],
    ) -> FeatureRunUc:
        return benchmark_run_features

    @staticmethod
    @inject
    def __run_algorithm_uc(
        benchmark_run_algorithms: AlgorithmRunUc = Provide[UsecaseContainer.benchmark_run_algorithm_uc],
    ) -> AlgorithmRunUc:
        return benchmark_run_algorithms

    @staticmethod
    @inject
    def __run_metric_uc(
        benchmark_run_metrics: MetricRunUc = Provide[UsecaseContainer.benchmark_run_metric_uc],
    ) -> MetricRunUc:
        return benchmark_run_metrics

    @staticmethod
    @inject
    def __create_uc(
        benchmark_create: BenchmarkCreateUc = Provide[UsecaseContainer.benchmark_create_uc],
    ) -> BenchmarkCreateUc:
        return benchmark_create

    @staticmethod
    @inject
    def __load_uc(
        benchmark_load: BenchmarkLoadUc = Provide[UsecaseContainer.benchmark_load_uc],
    ) -> BenchmarkLoadUc:
        return benchmark_load

    @staticmethod
    @inject
    def __load_all_uc(
        benchmark_load_all: BenchmarkLoadAllUc = Provide[UsecaseContainer.benchmark_load_all_uc],
    ) -> BenchmarkLoadAllUc:
        return benchmark_load_all

    @staticmethod
    @inject
    def __benchmark_set_modelset_uc(
        benchmark_set_modelset: BenchmarkSetModelsetUc = Provide[UsecaseContainer.benchmark_set_modelset_uc],
    ) -> BenchmarkSetModelsetUc:
        return benchmark_set_modelset

    @staticmethod
    @inject
    def __modelset_load_uc(
        modelset_load: ModelSetLoadUc = Provide[UsecaseContainer.modelset_load_uc],
    ) -> ModelSetLoadUc:
        return modelset_load

    @staticmethod
    @inject
    def __remove_modelset_uc(
        benchmark_remove_modelset: BenchmarkRemoveModelsetUc = Provide[UsecaseContainer.benchmark_remove_modelset_uc],
    ) -> BenchmarkRemoveModelsetUc:
        return benchmark_remove_modelset

    @staticmethod
    @inject
    def __remove_feature_uc(
        benchmark_remove_feature: FeatureRemoveUc = Provide[UsecaseContainer.benchmark_remove_feature_uc],
    ) -> FeatureRemoveUc:
        return benchmark_remove_feature

    @staticmethod
    @inject
    def __add_metric_uc(
        benchmark_add_metric_uc: MetricAddUc = Provide[UsecaseContainer.benchmark_add_metric_uc],
    ) -> MetricAddUc:
        return benchmark_add_metric_uc

    @staticmethod
    @inject
    def __add_feature_uc(
        benchmark_add_feature: FeatureAddUc = Provide[UsecaseContainer.benchmark_add_feature_uc],
    ) -> FeatureAddUc:
        return benchmark_add_feature

    @staticmethod
    @inject
    def __remove_metric_uc(
        benchmark_remove_metric: MetricRemoveUc = Provide[UsecaseContainer.benchmark_remove_metric_uc],
    ) -> MetricRemoveUc:
        return benchmark_remove_metric

    @staticmethod
    @inject
    def __add_algorithm_uc(
        benchmark_add_algorithm: AlgorithmAddUc = Provide[UsecaseContainer.benchmark_add_algorithm_uc],
    ) -> AlgorithmAddUc:
        return benchmark_add_algorithm

    @staticmethod
    @inject
    def __remove_algorithm_uc(
        benchmark_remove_algorithm: AlgorithmRemoveUc = Provide[UsecaseContainer.benchmark_remove_algorithm_uc],
    ) -> AlgorithmRemoveUc:
        return benchmark_remove_algorithm

    @staticmethod
    @inject
    def __add_plot_uc(
        benchmark_add_plot: PlotAddUc = Provide[UsecaseContainer.benchmark_add_plot_uc],
    ) -> PlotAddUc:
        return benchmark_add_plot

    @staticmethod
    @inject
    def __remove_plot_uc(
        benchmark_remove_plot: PlotRemoveUc = Provide[UsecaseContainer.benchmark_remove_plot_uc],
    ) -> PlotRemoveUc:
        return benchmark_remove_plot

    @staticmethod
    def create(
        name: str,
    ) -> Benchmark:
        """
        Create a new benchmark with the given name.

        The name for a benchmark must be unique. The returned Benchmark object can be used to interact and configure
        the new benchmark.

        Parameters
        ----------
        name: str
            The name of the new benchmark.

        Returns
        -------
        Benchmark
            The newly created Benchmark object.

        """
        benchmark_create = Benchmark.__create_uc()
        result: Result[
            BenchmarkEntity, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = benchmark_create(name)

        if not is_successful(result):
            error = result.failure()

            match error:
                case DataNotUniqueError():
                    Benchmark._logger.warning(
                        f"Benchmark '{name}' does already exist. Loading it with `Benchmark.load(\"{name}\")`."
                    )
                    return Benchmark.load(name)
                case _:
                    Benchmark._logger.error(f"Failed to create benchmark: {error}")
                    raise RuntimeError(error)

        return Benchmark.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    def open(name: str) -> Benchmark:
        """
        Load a benchmark if it exists, otherwise create a new one.

        Parameters
        ----------
        name: str
            The name of the benchmark.

        Returns
        -------
        Benchmark
            The loaded or newly created Benchmark object.

        """
        benchmark_load = Benchmark.__load_uc()
        result: Result[
            BenchmarkEntity, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = benchmark_load(name)

        if is_successful(result):
            return Benchmark.model_validate(result.unwrap(), from_attributes=True)

        if not isinstance(result.failure(), DataNotExistError):
            error = result.failure()
            Benchmark._logger.error(f"Failed to open benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        return Benchmark.create(name)

    @staticmethod
    def import_from_file(file_path: str) -> Benchmark:  # noqa: D102 # Not yet implemented
        raise NotImplementedError  # pragma: no cover

    def delete(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def load(name: str) -> Benchmark:
        """
        Load a benchmark from the database by its name.

        Parameters
        ----------
        name: str
            The name of the benchmark to load.

        Returns
        -------
        Benchmark
            The loaded Benchmark object.

        """
        benchmark_load = Benchmark.__load_uc()
        result: Result[
            BenchmarkEntity, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = benchmark_load(name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to load benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        return Benchmark.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    def load_all() -> list[Benchmark]:
        """
        Load all benchmarks from the database.

        Loading all benchmarks from the database can be a slow operation and should be used sparingly.

        Returns
        -------
        list[Benchmark]
            A list of Benchmark objects representing all benchmarks in the database. If no benchmarks are found,
            an empty list is returned.

        """
        benchmark_load_all = Benchmark.__load_all_uc()
        result: Result[list[BenchmarkEntity], UnknownLunaBenchError | UnknownIdError | ValidationError] = (
            benchmark_load_all()
        )
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to load all benchmarks: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        ta = TypeAdapter(list[Benchmark])
        return ta.validate_python(result.unwrap(), from_attributes=True)

    def reset(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError  # pragma: no cover

    def export_to_file(self, file_path: str) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError  # pragma: no cover

    def set_modelset(
        self,
        modelset: str | ModelSet,
    ) -> None:
        """
        Set the modelset for the benchmark.

        This method sets the modelset for the benchmark. Changing the modelset can affect the results of the benchmark.
        Therfore its recommended to not change the modelset after the benchmark has been created. If it is necessary,
        the results of the benchmark should be deleted and the benchmark itself should be re-run.

        Parameters
        ----------
        modelset: str | ModelSet
            Set the modelset for the benchmark to this modelset. It can be the name of the modelset or the modelset
            itself.

        """
        benchmark_set_modelset = self.__benchmark_set_modelset_uc()

        if isinstance(modelset, str):
            modelset = ModelSet.load(modelset)

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_set_modelset(
            self.name, modelset.name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to set modelset for benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self.modelset = modelset

    def remove_modelset(
        self,
    ) -> None:
        """
        Remove the modelset from the benchmark.

        This method removes the modelset from the benchmark. If the modelset is not set, this method does nothing. After
        removing the modelset, the results of the benchmark may be invalid.j

        """
        if not self.modelset:
            return

        benchmark_remove_modelset = self.__remove_modelset_uc()

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_modelset(self.name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove modelset for benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        self.modelset = None

    def get_feature(self, name: str) -> FeatureEntity:
        """
        Get a feature by its name from a benchmark.

        If the feature is not present, an error will be raised.

        Parameters
        ----------
        name: str
            The name of the feature to be retrieved.

        Raises
        ------
        DataNotExistError
            Raised if its name couldn't retrieve the feature.

        """
        for feature in self.features:
            if feature.name == name:
                return feature
        raise DataNotExistError

    def add_feature(
        self,
        name: str,
        feature: BaseFeature,
    ) -> FeatureEntity:
        """
        Add a feature to the benchmark with a given name.

        This method adds a feature to the benchmark. The name must be unique within the benchmark.
        When the benchmark is rerun, the feature will be used to calculate the metrics for each algorithm result.

        Also, the feature must be defined in the registry. If this isn't the case, an error will be received.
        To fix this, please check the documentation on how to do this.

        Parameters
        ----------
        name: str
            Name of the feature to add.
        feature: Feature
            The feature to add.

        Returns
        -------
        Feature
            The added feature.
        """
        benchmark_add_feature = self.__add_feature_uc()

        result: Result[
            FeatureEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_feature(self.name, name, feature)
        if not is_successful(result):
            error = result.failure()

            match error:
                case DataNotUniqueError():
                    Benchmark._logger.warning(
                        f"Feature '{name}' does already exist for this benchmark. "
                        f'Loading it with `benchmark.get_feature("{name}")`.'
                    )
                    return self.get_feature(name)
                case _:
                    Benchmark._logger.error(f"Failed to add feature to benchmark: {error}")

                    if isinstance(error, UnknownLunaBenchError):
                        raise error.error()
                    raise error

        unwrapped_result = result.unwrap()
        self.features.append(unwrapped_result)
        return unwrapped_result

    def remove_feature(
        self,
        feature: str | FeatureEntity,
    ) -> None:
        """
        Remove a feature from the benchmark.

        Parameters
        ----------
        feature: str | FeatureEntity
            The name of the feature to remove or the feature object itself. Make sure to use the ``FeatureUserModel``
            object and not only an ``IFeature`` object. This is important because the feature name is used to identify
            the feature.

        """
        benchmark_remove_feature = self.__remove_feature_uc()
        feature_name = feature.name if isinstance(feature, FeatureEntity) else feature

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_feature(
            self.name, feature_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove feature from benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self._remove_name_from_list(self.features, feature_name)

    def get_metric(self, name: str) -> MetricEntity:
        """
        Get a metric by its name from a benchmark.

        If the metric is not present, an error will be raised.

        Parameters
        ----------
        name: str
            The name of the metric to be retrieved.

        Raises
        ------
        DataNotExistError
            Raised if its name couldn't retrieve the metric.

        """
        for metric in self.metrics:
            if metric.name == name:
                return metric
        raise DataNotExistError

    def add_metric(
        self,
        name: str,
        metric: BaseMetric,
    ) -> MetricEntity:
        """
        Add a metric to the benchmark with a given name.

        This method adds a metric to the benchmark. The name must be unique within the benchmark. When the benchmark is
        rerun, the metric will be calculated for each algorithm result.

        Also, the metric must be defined in the registry. If this isn't the case, an error will be received.
        To fix this, please check the documentation on how to do this.

        Parameters
        ----------
        name: str
            The name of the metric to add.
        metric: Metric
            An instance of the metric to add.

        Returns
        -------
        Metric
            The added metric.
        """
        benchmark_add_metric_uc = self.__add_metric_uc()
        result: Result[
            MetricEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_metric_uc(self.name, name, metric)
        if not is_successful(result):
            error = result.failure()

            match error:
                case DataNotUniqueError():
                    Benchmark._logger.warning(
                        f"Metric '{name}' does already exist for this benchmark. "
                        f'Loading it with `benchmark.get_metric("{name}")`.'
                    )
                    return self.get_metric(name)
                case _:
                    Benchmark._logger.error(f"Failed to add metric to benchmark: {error}")
                    if isinstance(error, UnknownLunaBenchError):
                        raise error.error()
                    raise error

        unwrapped_result = result.unwrap()
        self.metrics.append(unwrapped_result)
        return unwrapped_result

    def remove_metric(
        self,
        metric: str | MetricEntity,
    ) -> None:
        """
        Remove a metric from the benchmark.

        Parameters
        ----------
        metric: str | MetricEntity
            The name of the metric to remove or the metric object itself. Make sure to use the ``MetricUserModel``
            object and not only an ``IMetric`` object. This is important because the metric name is used to identify
            the metric.
        """
        benchmark_remove_metric = self.__remove_metric_uc()
        metric_name = metric.name if isinstance(metric, MetricEntity) else metric

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_metric(
            self.name, metric_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove metric from benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self._remove_name_from_list(self.metrics, metric_name)

    def get_algorithm(self, name: str) -> AlgorithmEntity:
        """
        Get an algorithm by its name from a benchmark.

        If the algorithm is not present, an error will be raised.

        Parameters
        ----------
        name: str
            The name of the algorithm to be retrieved.

        Raises
        ------
        DataNotExistError
            Raised if its name couldn't retrieve the feature.

        """
        for algorithm in self.algorithms:
            if algorithm.name == name:
                return algorithm
        raise DataNotExistError

    def add_algorithm(
        self,
        name: str,
        algorithm: IAlgorithm[Any] | BaseAlgorithmSync | BaseAlgorithmAsync[Any],
    ) -> AlgorithmEntity:
        """
        Add an algorithm to the benchmark with a given name.

        This method adds an algorithm to the benchmark. The name must be unique within the benchmark. When the benchmark
        is rerun, the results for this algorithm will be calculated.

        Also, the algorithm must be defined in the registry. If this isn't the case, an error will be received.
        To fix this, please check the documentation on how to do this.

        Parameters
        ----------
        name: str
            The name of the algorithm to add.
        algorithm: IAlgorithm[Any] | AlgorithmSync | AlgorithmAsync[Any]
            An instance of the algorithm to add.

        Returns
        -------
        AlgorithmEntity
            The added algorithm.
        """
        if isinstance(algorithm, IAlgorithm):
            algorithm = LunaAlgorithmWrapper.wrap(algorithm)

        benchmark_add_algorithm = self.__add_algorithm_uc()
        result: Result[
            AlgorithmEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_algorithm(self.name, name, algorithm)

        if not is_successful(result):
            error = result.failure()

            match error:
                case DataNotUniqueError():
                    Benchmark._logger.warning(
                        f"Algorithm '{name}' does already exist for this benchmark. "
                        f'Loading it with `benchmark.get_algorithm("{name}")`.'
                    )
                    return self.get_algorithm(name)
                case _:
                    Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
                    if isinstance(error, UnknownLunaBenchError):
                        raise error.error()
                    raise error
        result_algorithm = result.unwrap()
        self.algorithms.append(result_algorithm)
        return result_algorithm

    def remove_algorithm(
        self,
        algorithm: str | AlgorithmEntity,
    ) -> None:
        """
        Remove an algorithm from the benchmark.

        Parameters
        ----------
        algorithm: str | AlgorithmEntity
            The name of the algorithm to remove or the algorithm object itself. Make sure to use the
            ``AlgorithmUserModel`` object and not only an ``IAlgorithm`` object.
            This is important because the algorithm name is used to identify the algorithm.
        """
        benchmark_remove_algorithm = self.__remove_algorithm_uc()
        algorithm_name = algorithm.name if isinstance(algorithm, AlgorithmEntity) else algorithm

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_algorithm(
            self.name, algorithm_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove algorithm from benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self._remove_name_from_list(self.algorithms, algorithm_name)

    def get_plot(self, name: str) -> PlotEntity:
        """
        Get a plot by its name from a benchmark.

        If the plot is not present, an error will be raised.

        Parameters
        ----------
        name: str
            The name of the algorithm to be retrieved.

        Raises
        ------
        DataNotExistError
            Raised if its name couldn't retrieve the plot.

        """
        for plot in self.plots:
            if plot.name == name:
                return plot
        raise DataNotExistError

    def add_plot(
        self,
        name: str,
        plot: BasePlot[Any],
    ) -> PlotEntity:
        """
        Add a plot to the benchmark with a given name.

        This method adds a plot to the benchmark. The name must be unique within the benchmark. When the benchmark
        is rerun, the results for this plot will be calculated.

        Also, the plot must be defined in the registry. If this isn't the case, an error will be received.
        To fix this, please check the documentation on how to do this.

        Parameters
        ----------
        name: str
            The name of the plot to add.
        plot: Plot[Any]
            The plot to add.

        Returns
        -------
        Plot
            The added plot.

        """
        benchmark_add_plot = self.__add_plot_uc()
        result: Result[
            PlotEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_plot(self.name, name, plot)
        if not is_successful(result):
            error = result.failure()

            match error:
                case DataNotUniqueError():
                    Benchmark._logger.warning(
                        f"Plot '{name}' does already exist for this benchmark. "
                        f'Loading it with `benchmark.get_plot("{name}")`.'
                    )
                    return self.get_plot(name)
                case _:
                    Benchmark._logger.error(f"Failed to add plot to benchmark: {error}")
                    if isinstance(error, UnknownLunaBenchError):
                        raise error.error()
                    raise error
        unwrapped_result = result.unwrap()
        self.plots.append(unwrapped_result)

        return unwrapped_result

    def remove_plot(
        self,
        plot: str | PlotEntity,
    ) -> None:
        """
        Remove a plot from the benchmark.

        Parameters
        ----------
        plot : str | Plot
            The name of the plot to remove or the plot object itself. Make sure to use the ``Plot``
            object and not only an ``IPlot`` object. This is important because the plot name is used to identify the
            plot.
        """
        benchmark_remove_plot = self.__remove_plot_uc()
        plot_name = plot.name if isinstance(plot, PlotEntity) else plot

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_plot(self.name, plot_name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove plot from benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self._remove_name_from_list(self.plots, plot_name)

    def run_features(self) -> None:
        """
        Calculate all configured features for all models of this benchmark.

        Parameters
        ----------
        benchmark_run_features: FeatureRunUc, inject
        """
        benchmark_run_features = self.__run_feature_uc()
        result: Result[None, RunFeatureMissingError | RunModelsetMissingError] = benchmark_run_features(self)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to run features for the benchmark: {error}")
            raise RuntimeError(error)

    def run_algorithms(self) -> None:
        """Calculate all configured features for all models of this benchmark."""
        benchmark_run_algorithms = self.__run_algorithm_uc()
        result: Result[None, RunAlgorithmMissingError | RunModelsetMissingError] = benchmark_run_algorithms(self)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to run algorithms for the benchmark: {error}")
            raise RuntimeError(error)

    def run_metrics(self) -> None:  # noqa: D102 # Not yet implemented
        benchmark_run_metrics = self.__run_metric_uc()
        result: Result[None, RunMetricMissingError | RunModelsetMissingError | RunFeatureMissingError] = (
            benchmark_run_metrics(self)
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to run metrics for the benchmark: {error}")
            raise RuntimeError(error)

    def run_plots(
        self,
        error_handling_mode: ErrorHandlingMode = ErrorHandlingMode.FAIL_ON_ERROR,
    ) -> None:
        """
        Execute all plots registered in the benchmark.

        Iterates through all plots in the benchmark, validates each plot against
        the benchmark data, and executes the plot generation. Each plot is
        validated before execution to ensure required data (metrics, features, etc.)
        is available. Plot execution is sequential and follows the order defined
        in the benchmark configuration.

        Parameters
        ----------
        error_handling_mode : ErrorHandlingMode
            Determines behavior when plot validation or execution fails.
            - FAIL_ON_ERROR: Stop at the first error and raise RuntimeError
            - CONTINUE_ON_ERROR: Log warnings and continue with remaining plots

        Raises
        ------
        RuntimeError
            If plot validation or execution fails. The RuntimeError wraps the
            underlying error, which may be PlotRunError (for validation failures)
            or UnknownLunaBenchError (for unexpected execution errors).
            Only raised in FAIL_ON_ERROR mode; in CONTINUE_ON_ERROR mode,
            errors are logged as warnings instead.

        Notes
        -----
        In FAIL_ON_ERROR mode, the method stops at the first validation or
        execution error. In CONTINUE_ON_ERROR mode, errors are logged and
        execution continues with remaining plots.
        """
        benchmark_run_plots = self.__run_plots_uc()
        result = benchmark_run_plots(self, UseCaseErrorHandlingMode(error_handling_mode.value))
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to run plots for the benchmark {self.name} with error: {error}")
            raise RuntimeError(error)

    def run(self) -> None:
        """Execute the benchmark."""
        self.run_features()
        self.run_algorithms()
        self.run_metrics()
        self.run_plots()

    def results_to_dataframe(self, *, inlcude_solution: bool = False) -> pd.DataFrame:
        """
        Return all benchmark results as a single DataFrame.

        Builds individual DataFrames for each feature (see ``.features_to_dataframe()``), algorithm
        (see ``.algorithms_to_dataframe``), and metric entity (see ``.metrics_to_dataframe()``),
        then merges them. Features merge on ``model``, metrics merge on
        ``(algorithm, model)``. Feature values are repeated across algorithms for the
        same model since features are model-level.

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns ``algorithm``, ``model``, plus one column per
            result field of each feature and metric.

        """
        if len(self.algorithms) == 0:
            msg = "Cannot build results DataFrame: no algorithm results available."
            raise ValueError(msg)
        exclude_cols = set() if inlcude_solution else {"solution"}
        algorithms_df = self.algorithms_to_dataframe(exclude=exclude_cols)

        features_df = self.all_features_to_dataframe()
        metrics_df = self.all_metrics_to_dataframe()

        return algorithms_df.merge(right=metrics_df, on=["algorithm", "model"], how="left").merge(
            right=features_df, on="model", how="left"
        )

    def _merge_result_entity(
        self,
        result_entities: list[ResultEntityT],
        on: list[str],
        entity_to_metric: Callable[[ResultEntityT], pd.DataFrame],
    ) -> pd.DataFrame:
        """Return all entity results merged into a single DataFrame on `defined on.."""
        result = pd.DataFrame(columns=on)
        for entity in result_entities:
            result = result.merge(
                entity_to_metric(entity),
                on=on,
                how="outer",
            )
        return result

    def features_to_dataframe(self, feature_entity: FeatureEntity) -> pd.DataFrame:
        """Return results for a single feature entity as a DataFrame with one row per model."""
        return self._resultsentity_to_dataframe(
            entity=feature_entity,
            key_columns=lambda model_name: {"model": model_name},
        )

    def all_features_to_dataframe(self) -> pd.DataFrame:
        """Return all feature results merged into a single DataFrame on ``model``."""
        return self._merge_result_entity(
            result_entities=self.features, on=["model"], entity_to_metric=self.features_to_dataframe
        )

    def metrics_to_dataframe(self, metric_entity: MetricEntity) -> pd.DataFrame:
        """Return results for a single metric entity as a DataFrame with one row per (algorithm, model)."""
        return self._resultsentity_to_dataframe(
            entity=metric_entity,
            key_columns=lambda key: {"algorithm": key[0], "model": key[1]},
        )

    def all_metrics_to_dataframe(self) -> pd.DataFrame:
        """Return all metric results merged into a single DataFrame on ``(algorithm, model)``."""
        return self._merge_result_entity(
            result_entities=self.metrics, on=["algorithm", "model"], entity_to_metric=self.metrics_to_dataframe
        )

    def _resultsentity_to_dataframe(
        self,
        entity: ResultEntityT,
        key_columns: Callable[[Any], dict[str, Any]],
    ) -> pd.DataFrame:
        """Flatten result entities into a DataFrame."""
        rows: list[dict[str, Any]] = []
        for key, result_entity in entity.results.items():
            row = key_columns(key)
            if result_entity.result is not None:
                for field_name, value in result_entity.result.model_dump().items():
                    row[f"{entity.name}/{field_name}"] = value
            rows.append(row)
        return pd.DataFrame(rows)

    def algorithms_to_dataframe(self, exclude: set[str] | None = None) -> pd.DataFrame:
        """Return all algorithm (algorithm, model) combinations as a DataFrame."""
        if exclude is None:
            exclude = set()
        rows: list[dict[str, Any]] = []
        for algo_entity in self.algorithms:
            for model_name, result_entity in algo_entity.results.items():
                row: dict[str, Any] = {
                    "algorithm": algo_entity.name,
                    "model": model_name,
                    **result_entity.result_dump(
                        exclude={"task_id", "status", "retrival_data", "error", "model_id", *exclude}
                    ),
                    "algorithm_config": algo_entity.algorithm.model_dump(),
                }
                rows.append(row)
        return pd.DataFrame(rows)

    def list_feature_classes(self) -> list[type[BaseFeature]]:
        """Return the feature classes registered on this benchmark."""
        return [type(m.feature) for m in self.features]

    def list_metrics_classes(self) -> list[type[BaseMetric]]:
        """Return the metric classes registered on this benchmark."""
        return [type(m.metric) for m in self.metrics]

    def list_plots_classes(self) -> list[type[BasePlot[Any]]]:
        """Return the plot classes registered on this benchmark."""
        return [type(p.plot) for p in self.plots]

    def list_algorithms(
        self,
    ) -> list[tuple[type[BaseAlgorithmSync | BaseAlgorithmAsync[Any]], dict[str, Any]]]:
        """Return the algorithm classes registered on this benchmark."""
        return [(type(a.algorithm), a.algorithm.model_dump()) for a in self.algorithms]

    def list_backends(self) -> list[None]:  # noqa: D102 # Not yet implemented
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def _remove_name_from_list[T: BaseModel](obj_list: list[T], name: str) -> None:
        for i, obj in enumerate(obj_list):
            if getattr(obj, "name", None) == name:
                del obj_list[i]
                # since we use name as a unique identifier,
                # we can break after the first match (only one name per list allowed).
                return
