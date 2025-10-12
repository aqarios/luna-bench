from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel, TypeAdapter, ValidationError
from returns.pipeline import is_successful

from luna_bench._internal.interfaces import IFeature, IMetric, IPlot
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmAddUc,
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
    PlotAddUc,
    PlotRemoveUc,
)
from luna_bench._internal.usecases.modelset.protocols import ModelSetLoadUc
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench._internal.user_models import (
    AlgorithmUserModel,
    BenchmarkUserModel,
    FeatureUserModel,
    MetricUserModel,
    PlotUserModel,
)
from luna_bench.components.algorithm import Algorithm
from luna_bench.components.feature import Feature
from luna_bench.components.metric import Metric
from luna_bench.components.model_set import ModelSet
from luna_bench.components.plot import Plot
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from logging import Logger

    from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
    from luna_quantum.solve.interfaces.backend_i import IBackend
    from returns.result import Result


class Benchmark(BenchmarkUserModel):
    """
    Benchmark class represents a benchmark in the LunaBench system.

    This class is responsible for managing benchmark-related operations, including creating and deleting benchmarks.
    It provides methods for interacting with the benchmark data and executing benchmark runs.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)

    @staticmethod
    @inject
    def create(
        name: str,
        benchmark_create: BenchmarkCreateUc = Provide[UsecaseContainer.benchmark_create_uc],  # Will be injected
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
        result: Result[
            BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = benchmark_create(name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to create benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        return Benchmark.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    def import_from_file(file_path: str) -> Benchmark:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def delete(self) -> None: ...  # noqa: D102 # Not yet implemented

    @staticmethod
    @inject
    def load(name: str, benchmark_load: BenchmarkLoadUc = Provide[UsecaseContainer.benchmark_load_uc]) -> Benchmark:
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
        result: Result[
            BenchmarkUserModel, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = benchmark_load(name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to load benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        return Benchmark.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    @inject
    def load_all(
        benchmark_load_all: BenchmarkLoadAllUc = Provide[UsecaseContainer.benchmark_load_all_uc],
    ) -> list[Benchmark]:
        """
        Load all benchmarks from the database.

        Loading all benchmarks from the database can be a slow operation and should be used sparingly.

        Returns
        -------
        list[Benchmark]
            A list of Benchmark objects representing all benchmarks in the database. If no benchmarks are found,
            an empty list is returned.

        """
        result: Result[list[BenchmarkUserModel], UnknownLunaBenchError | UnknownIdError | ValidationError] = (
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

    def run(self) -> None: ...  # noqa: D102 # Not yet implemented

    def reset(self) -> None: ...  # noqa: D102 # Not yet implemented

    def export_to_file(self, file_path: str) -> None: ...  # noqa: D102 # Not yet implemented

    @inject
    def set_modelset(
        self,
        modelset: str | ModelSet,
        benchmark_set_modelset: BenchmarkSetModelsetUc = Provide[UsecaseContainer.benchmark_set_modelset_uc],
        modelset_load: ModelSetLoadUc = Provide[UsecaseContainer.modelset_load_uc],
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
        modelset_name: str = modelset.name if isinstance(modelset, ModelSet) else modelset

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_set_modelset(
            self.name, modelset_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to set modelset for benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        result_modelset = modelset_load(modelset_name)

        if not is_successful(result_modelset):
            error = result_modelset.failure()
            Benchmark._logger.error(f"Failed to load modelset for benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        self.modelset = result_modelset.unwrap()

    @inject
    def remove_modelset(
        self,
        benchmark_remove_modelset: BenchmarkRemoveModelsetUc = Provide[UsecaseContainer.benchmark_remove_modelset_uc],
    ) -> None:
        """
        Remove the modelset from the benchmark.

        This method removes the modelset from the benchmark. If the modelset is not set, this method does nothing. After
        removing the modelset, the results of the benchmark may be invalid.j

        """
        if not self.modelset:
            return

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_modelset(self.name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove modelset for benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        self.modelset = None

    @inject
    def add_feature(
        self,
        name: str,
        feature: IFeature,
        benchmark_add_feature: FeatureAddUc = Provide[UsecaseContainer.benchmark_add_feature_uc],
    ) -> Feature:
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
        feature: IFeature
            The feature to add.

        Returns
        -------
        Feature
            The added feature.
        """
        result: Result[
            FeatureUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_feature(self.name, name, feature)
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add model metric to benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        self.features.append(result.unwrap())
        return Feature.model_validate(result.unwrap(), from_attributes=True)

    @inject
    def remove_feature(
        self,
        feature: str | Feature,
        benchmark_remove_feature: FeatureRemoveUc = Provide[UsecaseContainer.benchmark_remove_feature_uc],
    ) -> None:
        """
        Remove a feature from the benchmark.

        Parameters
        ----------
        feature: str | Feature
            The name of the feature to remove or the feature object itself. Make sure to use the ``Feature`` object and
            not only an ``IFeature`` object. This is important because the feature name is used to identify the
            feature.

        """
        feature_name = feature.name if isinstance(feature, Feature) else feature

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_feature(
            self.name, feature_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add model metric to benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self._remove_name_from_list(self.features, feature_name)

    @inject
    def add_metric(
        self,
        name: str,
        metric: IMetric,
        benchmark_add_metric_uc: MetricAddUc = Provide[UsecaseContainer.benchmark_add_metric_uc],
    ) -> Metric:
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
        metric: IMetric
            An instance of the metric to add.

        Returns
        -------
        Metric
            The added metric.
        """
        result: Result[
            MetricUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_metric_uc(self.name, name, metric)
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add metric to benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        self.metrics.append(result.unwrap())
        return Metric.model_validate(result.unwrap(), from_attributes=True)

    @inject
    def remove_metric(
        self,
        metric: str | Metric,
        benchmark_remove_metric: MetricRemoveUc = Provide[UsecaseContainer.benchmark_remove_metric_uc],
    ) -> None:
        """
        Remove a metric from the benchmark.

        Parameters
        ----------
        metric: str | Metric
            The name of the metric to remove or the metric object itself. Make sure to use the ``Metric`` object and
            not only an ``IMetric`` object. This is important because the metric name is used to identify the
            metric.
        """
        metric_name = metric.name if isinstance(metric, Metric) else metric

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_metric(
            self.name, metric_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add metric to benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self._remove_name_from_list(self.metrics, metric_name)

    @inject
    def add_algorithm(
        self,
        name: str,
        algorithm: IAlgorithm[IBackend],
        benchmark_add_algorithm: AlgorithmAddUc = Provide[UsecaseContainer.benchmark_add_algorithm_uc],
    ) -> Algorithm:
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
        algorithm: IAlgorithm
            An instance of the algorithm to add.

        Returns
        -------
        Algorithm
            The added algorithm.
        """
        result: Result[
            AlgorithmUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_algorithm(self.name, name, algorithm)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error
        result_algorithm = result.unwrap()
        self.algorithms.append(result_algorithm)
        return Algorithm.model_construct(
            name=result_algorithm.name,
            status=result_algorithm.status,
            algorithm=result_algorithm.algorithm,
        )

    def remove_algorithm(
        self,
        algorithm: str | Algorithm,
        benchmark_remove_algorithm: MetricRemoveUc = Provide[UsecaseContainer.benchmark_remove_algorithm_uc],
    ) -> None:
        """
        Remove an algorithm from the benchmark.

        Parameters
        ----------
        algorithm: str | Algorithm
            The name of the algorithm to remove or the algorithm object itself. Make sure to use the ``Algorithm``
            object and not only an ``IAlgorithm`` object. This is important because the algorithm name is used to
            identify the algorithm.
        """
        algorithm_name = algorithm.name if isinstance(algorithm, Algorithm) else algorithm

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_algorithm(
            self.name, algorithm_name
        )

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add algorithm to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.algorithms, algorithm_name)

    def add_plot(
        self,
        name: str,
        plot: IPlot,
        benchmark_add_plot: PlotAddUc = Provide[UsecaseContainer.benchmark_add_plot_uc],
    ) -> Plot:
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
        plot: IPlot
            The plot to add.

        Returns
        -------
        Plot
            The added plot.

        """
        result: Result[
            PlotUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = benchmark_add_plot(self.name, name, plot)
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to add plot to benchmark: {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        self.plots.append(result.unwrap())

        return Plot.model_validate(result.unwrap(), from_attributes=True)

    def remove_plot(
        self,
        plot: str | Plot,
        benchmark_remove_plot: PlotRemoveUc = Provide[UsecaseContainer.benchmark_remove_plot_uc],
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
        plot_name = plot.name if isinstance(plot, Plot) else plot

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_plot(self.name, plot_name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove plot to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.plots, plot_name)

    def run_features(
        self, benchmark_run_features: FeatureRunUc = Provide[UsecaseContainer.benchmark_run_feature_uc]
    ) -> None:
        """
        Calculate all configured features for all models of this benchmark.

        Parameters
        ----------
        benchmark_run_features: FeatureRunUc, inject
        """
        benchmark_run_features(self)

    def run_metrics(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def run_plots(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def run_jobs(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def list_model_metrics_classes(self) -> list[None]:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def list_metrics_classes(self) -> list[None]:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def list_plots_classes(self) -> list[None]:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def list_algorithms(self) -> list[None]:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    def list_backends(self) -> list[None]:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

    @staticmethod
    def _remove_name_from_list[T: BaseModel](obj_list: list[T], name: str) -> None:
        for i, obj in enumerate(obj_list):
            if getattr(obj, "name", None) == name:
                del obj_list[i]
                # since we use name as a unique identifier,
                # we can break after the first match (only one name per list allowed).
                return
