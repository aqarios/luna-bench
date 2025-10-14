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
        benchmark_remove_algorithm: MetricRemoveUc = Provide[UsecaseContainer.benchmark_remove_algorithm_uc],
    ) -> MetricRemoveUc:
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
        modelset_load = self.__modelset_load_uc()

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

    def add_feature(
        self,
        name: str,
        feature: IFeature,
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
        benchmark_add_feature = self.__add_feature_uc()

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

    def remove_feature(
        self,
        feature: str | Feature,
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
        benchmark_remove_feature = self.__remove_feature_uc()
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

    def add_metric(
        self,
        name: str,
        metric: IMetric,
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
        benchmark_add_metric_uc = self.__add_metric_uc()
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

    def remove_metric(
        self,
        metric: str | Metric,
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
        benchmark_remove_metric = self.__remove_metric_uc()
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

    def add_algorithm(
        self,
        name: str,
        algorithm: IAlgorithm[IBackend],
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
        benchmark_add_algorithm = self.__add_algorithm_uc()
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
        benchmark_remove_algorithm = self.__remove_algorithm_uc()
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
        benchmark_add_plot = self.__add_plot_uc()
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
        plot_name = plot.name if isinstance(plot, Plot) else plot

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_remove_plot(self.name, plot_name)

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to remove plot to benchmark: {error}")
            raise RuntimeError(error)

        self._remove_name_from_list(self.plots, plot_name)

    def run_model_metrics(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError

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
