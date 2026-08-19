from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from dependency_injector.wiring import Provide, inject
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from pydantic import BaseModel, TypeAdapter, ValidationError
from returns.pipeline import is_successful

from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench._internal.wrappers import LunaAlgorithmWrapper
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    FeatureEntity,
    MetricEntity,
    PlotEntity,
)
from luna_bench.entities.enums import ResetLevel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.modelset_not_loaded_error import ModelSetNotLoadedError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.logging import BenchLogger
from luna_bench.model_set import MODEL_FILE_SUFFIXES, ModelSet, ModelSource

if TYPE_CHECKING:
    from collections.abc import Iterable
    from logging import Logger

    import pandas as pd
    from returns.result import Result

    from luna_bench._internal.usecases.benchmark.protocols import (
        AlgorithmAddUc,
        AlgorithmRemoveUc,
        AlgorithmRunUc,
        BenchmarkCreateUc,
        BenchmarkExportUc,
        BenchmarkLoadAllUc,
        BenchmarkLoadUc,
        BenchmarkRemoveModelsetUc,
        BenchmarkResetUc,
        BenchmarkSetModelsetUc,
        DataDirSetupUc,
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
    from luna_bench.custom import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot, Exporter
    from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
    from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
    from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
    from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
    from luna_bench.exporters import CsvQuoting, JsonOrient


class Benchmark(BenchmarkEntity):
    """
    Benchmark class represents a benchmark in the LunaBench system.

    This class is responsible for managing benchmark-related operations, including creating and deleting benchmarks.
    It provides methods for interacting with the benchmark data and executing benchmark runs.
    """

    _logger: ClassVar[Logger] = BenchLogger.get_logger(__name__)

    @staticmethod
    @inject
    def __run_plots_uc(
        benchmark_run_plots: PlotsRunUc = Provide[UsecaseContainer.benchmark_run_plots_uc],
    ) -> PlotsRunUc:
        return benchmark_run_plots

    @staticmethod
    @inject
    def __data_dir_setup_uc(
        benchmark_setup: DataDirSetupUc = Provide[UsecaseContainer.benchmark_setup_data_dir_uc],
    ) -> DataDirSetupUc:
        return benchmark_setup

    @staticmethod
    @inject
    def __export_uc(
        benchmark_export: BenchmarkExportUc = Provide[UsecaseContainer.benchmark_export_uc],
    ) -> BenchmarkExportUc:
        return benchmark_export

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
    @inject
    def __reset_uc(
        benchmark_reset: BenchmarkResetUc = Provide[UsecaseContainer.benchmark_reset_uc],
    ) -> BenchmarkResetUc:
        return benchmark_reset

    @staticmethod
    def _setup_data_dir(
        benchmark: BenchmarkEntity,
    ) -> None:
        """Set up the data directory for a benchmark and update the config path.

        This is called early (from ``open`` / ``create`` / ``load``) so that
        ``config.LB_DATA_DIR`` is resolved to an absolute path **before** any
        code that creates files (database, Huey jobs DB, etc.) runs with a stale
        default.
        """
        setup_uc = Benchmark.__data_dir_setup_uc()
        result = setup_uc(benchmark)
        if not is_successful(result):
            Benchmark._logger.warning("Output setup failed: %s", result.failure())
        # Set up file logging to the benchmark's logs directory.
        elif benchmark.data_dir_logs:
            BenchLogger.setup_file_logging(benchmark.data_dir_logs)

    def _promote_modelset(self) -> None:
        """Replace a data-only modelset with a live ``ModelSet`` handle.

        A benchmark read from the database carries its modelset as a plain
        ``ModelSetEntity``. Acquiring the live handle here means models can be
        added to and removed from any benchmark, however it was obtained.

        A modelset that cannot be loaded is left as data: the benchmark itself
        stays usable, and the failure surfaces as ``ModelSetNotLoadedError``
        only if models are actually added or removed.
        """
        if self.modelset is None or isinstance(self.modelset, ModelSet):
            return

        modelset_name = self.modelset.name
        try:
            self.modelset = ModelSet.load(modelset_name)
        except RuntimeError as error:
            Benchmark._logger.warning(
                f"Benchmark '{self.name}' references modelset '{modelset_name}', which could not be loaded: {error}"
            )

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
                    Benchmark._logger.warning(f"Loading existing benchmark ('{name}').")
                    return Benchmark.load(name)
                case _:
                    Benchmark._logger.error(f"Failed to create benchmark: {error}")
                    if isinstance(error, UnknownLunaBenchError):
                        raise error.error()
                    raise error

        benchmark = Benchmark.model_validate(result.unwrap(), from_attributes=True)
        Benchmark._setup_data_dir(benchmark)
        return benchmark

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
            benchmark = Benchmark.model_validate(result.unwrap(), from_attributes=True)
            Benchmark._setup_data_dir(benchmark)
            benchmark._promote_modelset()  # noqa: SLF001
            return benchmark

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

        result_entity = Benchmark.model_validate(result.unwrap(), from_attributes=True)
        Benchmark._setup_data_dir(result_entity)
        result_entity._promote_modelset()  # noqa: SLF001
        return result_entity

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

    def reset(self, *, mode: ResetLevel | Literal["All", "Unfinished", "Failed"]) -> None:
        """Clear results for the benchmark.

        Removes algorithm, metric, and feature results from the database.
        Metric results are cascaded (cleared along with algorithms). After
        the operation, the entity is reloaded from the database so its
        in-memory state is fully consistent.

        Parameters
        ----------
        mode: ResetLevel | Literal["All", "Unfinished", "Failed"]
            ``ResetLevel.ALL`` or ``"All"`` clears all results unconditionally.
            ``ResetLevel.UNFINISHED`` or ``"Unfinished"`` clears only non-DONE
            results (includes failed).
            ``ResetLevel.FAILED`` or ``"Failed"`` clears only FAILED results.
            No default — must be explicitly provided.
        """
        benchmark_reset = self.__reset_uc()
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = benchmark_reset(self, mode=ResetLevel(mode))

        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to reset benchmark '{self.name}': {error}")
            if isinstance(error, UnknownLunaBenchError):
                raise error.error()
            raise error

        fresh = Benchmark.load(self.name)
        self.__dict__.update(fresh.__dict__)

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

    def _resolve_modelset(self, *, create: bool = False) -> ModelSet:
        """
        Return this benchmark's modelset as a usable ``ModelSet`` handle.

        Parameters
        ----------
        create: bool
            If True and no modelset is configured, create one named after this
            benchmark and attach it. If False, a missing modelset is an error.
            Defaults to False.

        Returns
        -------
        ModelSet
            The modelset attached to this benchmark.

        Raises
        ------
        DataNotExistError
            Raised if no modelset is configured and ``create`` is False.
        ModelSetNotLoadedError
            Raised if the benchmark holds its modelset as data only and that
            modelset cannot be loaded from the database.
        """
        if self.modelset is None:
            if not create:
                msg = (
                    f"Benchmark '{self.name}' has no modelset, so it holds no models. "
                    f"Add models with `benchmark.add_model(...)`, or attach an existing "
                    f"modelset with `benchmark.set_modelset(...)`."
                )
                raise DataNotExistError(msg)
            modelset = ModelSet.create(self.name)
            if modelset.models:
                # ModelSet.create falls back to loading when the name is taken,
                # so this benchmark just adopted a modelset somebody else filled
                # - possibly one another benchmark is using.
                held = [m.name for m in modelset.models]
                Benchmark._logger.warning(
                    f"Benchmark '{self.name}' had no modelset and adopted the existing modelset "
                    f"'{modelset.name}', which already holds {len(held)} model(s): {held}. "
                    f"Attach a different one with `benchmark.set_modelset(...)` if that is not intended."
                )
            self.set_modelset(modelset)
            return modelset

        if isinstance(self.modelset, ModelSet):
            return self.modelset

        modelset_name = self.modelset.name
        self._promote_modelset()
        if isinstance(self.modelset, ModelSet):
            return self.modelset

        raise ModelSetNotLoadedError(self.name, modelset_name)

    def add_model(
        self,
        model: ModelSource,
        *,
        suffixes: Iterable[str] = MODEL_FILE_SUFFIXES,
    ) -> None:
        """
        Add a model to this benchmark's modelset.

        Convenience wrapper around ``ModelSet.add``. If the benchmark has no
        modelset yet, one named after the benchmark is created and attached, so
        ``Benchmark.create("my_bench").add_model(m)`` puts ``m`` into the
        modelset ``"my_bench"``. This modelset is created even if ``model`` is
        an empty iterable, so ``add_model([])`` on a benchmark with no modelset
        still creates and attaches an empty one named after the benchmark.

        Models already in the modelset are skipped with a warning rather than
        duplicated, so the same script can be run again safely.

        Parameters
        ----------
        model: ModelSource
            The model to add. It can be

            - a ``Model``,
            - a path (``str`` or ``Path``) to a model file. ``.lp`` and ``.mps``
              are read as such; any other suffix is read as a model encoded with
              ``Model.encode``,
            - a path to a directory, in which case every file whose suffix is in
              ``suffixes`` is added, in file-name order,
            - an iterable mixing any of the above, nested to any depth, in
              which case all of them are added.

            Models loaded from a file are named after the file stem, not after
            the name recorded inside the file.
        suffixes: Iterable[str]
            Which file suffixes a *directory* scan picks up. Defaults to
            ``(".lp", ".mps")``. A leading dot is optional, so ``"mps"`` works.
            Matching is case-sensitive, as it is in ``Model.from_``. This never
            filters a file named outright.

        Raises
        ------
        FileNotFoundError
            Raised if a given path does not exist, or is a directory holding no
            file with one of ``suffixes``.
        ValueError
            Raised if ``suffixes`` is empty, or if a given file is neither an
            ``.lp``/``.mps`` file nor an encoded model.
        ModelSetNotLoadedError
            Raised if this benchmark's modelset cannot be loaded from the
            database.
        ModelNameAlreadyUsedError
            Raised if a different model already uses the same name.
        """
        self._resolve_modelset(create=True).add(model, suffixes=suffixes)

    def remove_model(
        self,
        model: ModelSource,
        *,
        suffixes: Iterable[str] = MODEL_FILE_SUFFIXES,
    ) -> None:
        """
        Remove a model from this benchmark's modelset.

        Convenience wrapper around ``ModelSet.remove_model``. Unlike
        ``add_model``, this never creates a modelset.

        Parameters
        ----------
        model: ModelSource
            The model to remove. It accepts everything ``add_model`` accepts: a
            ``Model``, a path to a model file, a path to a directory of such
            files, or an iterable of those.
        suffixes: Iterable[str]
            Which file suffixes a *directory* scan picks up, as in ``add_model``.
            Pass the same value here that was passed to ``add_model``, or the
            models added from a directory will not be found again.

        Raises
        ------
        DataNotExistError
            Raised if no modelset is configured for this benchmark.
        FileNotFoundError
            Raised if a given path does not exist, or is a directory holding no
            file with one of ``suffixes``.
        ValueError
            Raised if ``suffixes`` is empty, or if a given file is neither an
            ``.lp``/``.mps`` file nor an encoded model.
        ModelSetNotLoadedError
            Raised if this benchmark's modelset cannot be loaded from the
            database.
        RuntimeError
            Raised if the model (or one of the models, for an iterable) is not
            part of the modelset.
        """
        self._resolve_modelset().remove_model(model, suffixes=suffixes)

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
        feature: BaseFeature[Any],
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
                    Benchmark._logger.warning(f"Loading existing feature ('{name}').")
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
                    Benchmark._logger.warning(f"Loading existing metric ('{name}').")
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
                    Benchmark._logger.warning(f"Loading existing Algorithm ('{name}').")
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
        plot: BasePlot,
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
                    Benchmark._logger.warning(f"Loading existing plot ('{name}').")
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
        """Calculate all configured features for all models of this benchmark."""
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
    ) -> None:
        """
        Execute all plots registered in the benchmark.

        Iterates through all plots in the benchmark, validates each plot against
        the benchmark data, and executes the plot generation. Each plot is
        validated before execution to ensure required data (metrics, features, etc.)
        is available. Plot execution is sequential and follows the order defined
        in the benchmark configuration.

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
        result = benchmark_run_plots(self)
        if not is_successful(result):
            error = result.failure()
            Benchmark._logger.error(f"Failed to run plots for the benchmark {self.name} with error: {error}")
            raise RuntimeError(error)

    def add_dependencies(self) -> None:
        """Add any required dependencies for the benchmark execution."""
        required_features: set[str] = {f.feature.registered_id for f in self.features}
        required_metrics: set[str] = {m.metric.registered_id for m in self.metrics}

        for p in self.plots:
            for m in p.plot.required_metrics:
                if m.registered_id not in required_metrics:
                    Benchmark._logger.info(f"Adding metric {m.registered_id} to benchmark {self.name}")
                    self.add_metric(m.registered_id, m())
                    required_metrics.add(m.registered_id)
            for f in p.plot.required_features:
                if f.registered_id not in required_features:
                    Benchmark._logger.info(f"Adding feature {f.registered_id} to benchmark {self.name}")
                    self.add_feature(f.registered_id, f())
                    required_features.add(f.registered_id)
        for metric in self.metrics:
            for f in metric.metric.required_features:
                if f.registered_id not in required_features:
                    Benchmark._logger.info(f"Adding feature {f.registered_id} to benchmark {self.name}")
                    self.add_feature(f.registered_id, f())
                    required_features.add(f.registered_id)

    def run(self, *, retry_uncompleted: bool = False) -> None:
        """Execute the benchmark.

        Parameters
        ----------
        retry_uncompleted: bool
            If True, clear only non-DONE (uncompleted) results before running
            so that failed or incomplete components are retried while DONE
            results are preserved. Defaults to False.
        """
        if retry_uncompleted:
            self.reset(mode="Unfinished")

        setup_uc = self.__data_dir_setup_uc()
        result = setup_uc(self)
        if not is_successful(result):
            Benchmark._logger.warning("Output setup failed: %s", result.failure())

        self.add_dependencies()
        self.run_features()
        self.run_algorithms()
        self.run_metrics()
        self.run_plots()

    def export[T](self, exporter: Exporter[T]) -> T:
        """
        Export all benchmark results using the given exporter strategy.

        Builds a full ``BenchmarkResultContainer`` (all feature, metric, and
        algorithm results of this benchmark) and hands it to the exporter. Any
        object implementing the ``Exporter`` protocol can be used, so custom
        export formats do not require changes to this class::

            benchmark.export(CsvExporter(delimiter=";"))  # built-in exporter
            benchmark.export(MyArrowExporter())  # custom exporter

        Parameters
        ----------
        exporter: Exporter[T]
            The exporter strategy that converts benchmark results into the
            target format.

        Returns
        -------
        T
            The exported payload, e.g. ``str`` for CSV/JSON or a
            ``pd.DataFrame`` for the DataFrame exporter.

        """
        export_uc = self.__export_uc()
        return export_uc(self, exporter)

    def to_csv(
        self,
        path: str | Path | None = None,
        *,
        delimiter: str = ",",
        quoting: CsvQuoting = "minimal",
        include_solution: bool = False,
    ) -> str | None:
        """
        Render all benchmark results as CSV.

        Convenience wrapper for ``self.export(CsvExporter(...))``. Mirrors
        ``pandas.DataFrame.to_csv``: if ``path`` is given, the CSV is written
        to that file and ``None`` is returned; otherwise the CSV is returned
        as a string.

        Parameters
        ----------
        path: str | Path | None
            File path to write the CSV to. If None, the CSV is returned as a
            string instead. Defaults to None.
        delimiter: str
            Field delimiter. Defaults to ``","``.
        quoting: CsvQuoting
            Quoting style: ``"minimal"``, ``"all"``, ``"nonnumeric"``, or ``"none"``.
            Defaults to ``"minimal"``.
        include_solution: bool
            Whether to include the serialized solution column (base64-encoded).
            Defaults to False.

        Returns
        -------
        str | None
            The benchmark results rendered as CSV, or ``None`` if written to
            ``path``.

        """
        from luna_bench.exporters import CsvExporter  # noqa: PLC0415

        payload = self.export(CsvExporter(delimiter=delimiter, quoting=quoting, include_solution=include_solution))
        if path is None:
            return payload
        Path(path).write_text(payload, encoding="utf-8")
        return None

    def to_json(
        self,
        path: str | Path | None = None,
        *,
        indent: int | None = None,
        orient: JsonOrient = "records",
        include_solution: bool = False,
    ) -> str | None:
        """
        Render all benchmark results as JSON.

        Convenience wrapper for ``self.export(JsonExporter(...))``. Mirrors
        ``pandas.DataFrame.to_json``: if ``path`` is given, the JSON is
        written to that file and ``None`` is returned; otherwise the JSON is
        returned as a string.

        Parameters
        ----------
        path: str | Path | None
            File path to write the JSON to. If None, the JSON is returned as
            a string instead. Defaults to None.
        indent: int | None
            Indentation width for pretty-printing; ``None`` for compact output.
            Defaults to ``None``.
        orient: JsonOrient
            JSON layout passed to ``DataFrame.to_json``. Defaults to ``"records"``.
        include_solution: bool
            Whether to include the serialized solution column (base64-encoded).
            Defaults to False.

        Returns
        -------
        str | None
            The benchmark results rendered as JSON, or ``None`` if written to
            ``path``.

        """
        from luna_bench.exporters import JsonExporter  # noqa: PLC0415

        payload = self.export(JsonExporter(indent=indent, orient=orient, include_solution=include_solution))
        if path is None:
            return payload
        Path(path).write_text(payload, encoding="utf-8")
        return None

    def plot_summary(  # noqa: PLR0913
        self,
        *,
        columns: int | None = None,
        rows: int | None = None,
        save_dir: str | None = None,
        figure_filename: str = "summary",
        file_formats: tuple[str, ...] | str = ("png",),
        show: bool = True,
        title: str | None = None,
    ) -> list[Path]:
        """
        Draw every plot of this benchmark into a single figure, one panel each.

        Convenience wrapper for ``luna_bench.plots.plot_summary(self, ...)``, which is
        also usable on its own. Run the benchmark first: the panels are drawn from the
        results it holds, and a plot that cannot be drawn is logged and left out rather
        than stopping the figure.

        Parameters
        ----------
        columns: int | None
            Number of columns of the grid. By default derived from ``rows``, or from the
            number of plots so the grid stays roughly square.
        rows: int | None
            Number of rows of the grid. By default as many as ``columns`` needs.
        save_dir: str | None
            Directory to write the figure into. Defaults to the benchmark's own plots
            directory, and to nowhere if the benchmark has none.
        figure_filename: str
            Stem of the written files. Defaults to ``"summary"``.
        file_formats: tuple[str, ...] | str
            Output formats written to ``save_dir``, one file each. Defaults to ``("png",)``.
        show: bool
            Whether to open the figure in a window. Defaults to True.
        title: str | None
            Title above the grid. Defaults to the name of the benchmark.

        Returns
        -------
        list[Path]
            The files that were written.

        Examples
        --------
        >>> bench.run()
        >>> bench.plot_summary(columns=3, show=False)
        """
        from luna_bench.plots import plot_summary  # noqa: PLC0415

        return plot_summary(
            self,
            columns=columns,
            rows=rows,
            save_dir=save_dir if save_dir is not None else self.data_dir_plots,
            figure_filename=figure_filename,
            file_formats=file_formats,
            show=show,
            title=title,
        )

    def to_dataframe(self, *, include_solution: bool = False) -> pd.DataFrame:
        """
        Return all benchmark results as a single DataFrame.

        Convenience wrapper for ``self.export(DataFrameExporter(...))``: algorithm
        results form the row spine (one row per ``(algorithm, model)``), metrics
        merge on ``(algorithm, model)``, and features merge on ``model``. Feature
        values are repeated across algorithms for the same model since features
        are model-level.

        Parameters
        ----------
        include_solution: bool
            Whether to include the serialized solution as a ``solution`` column.
            Defaults to False.

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns ``algorithm``, ``model``, plus one column per
            result field of each feature and metric.

        """
        from luna_bench.exporters import DataFrameExporter  # noqa: PLC0415

        return self.export(DataFrameExporter(include_solution=include_solution))

    def list_feature_classes(self) -> list[type[BaseFeature]]:
        """Return the feature classes registered on this benchmark."""
        return [type(m.feature) for m in self.features]

    def list_metrics_classes(self) -> list[type[BaseMetric]]:
        """Return the metric classes registered on this benchmark."""
        return [type(m.metric) for m in self.metrics]

    def list_plots_classes(self) -> list[type[BasePlot]]:
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
                # SINCE we use name as a unique identifier,
                # we can break after the first match (only one name per list allowed).
                return
