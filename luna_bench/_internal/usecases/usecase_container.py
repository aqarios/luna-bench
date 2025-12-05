from dependency_injector import containers, providers
from dependency_injector.providers import Configuration, Provider

from luna_bench._internal.dao import DaoContainer
from luna_bench._internal.mappers.container import MapperContainer
from luna_bench._internal.usecases.background_tasks.background_retrieve_algorithm_async import (
    BackgroundRetrieveAlgorithmAsyncUcImpl,
)
from luna_bench._internal.usecases.background_tasks.background_retrieve_algorithm_sync import (
    BackgroundRetrieveAlgorithmSyncUcImpl,
)
from luna_bench._internal.usecases.background_tasks.background_run_algorithm_async import (
    BackgroundRunAlgorithmAsyncUcImpl,
)
from luna_bench._internal.usecases.background_tasks.background_run_algorithm_sync import (
    BackgroundRunAlgorithmSyncUcImpl,
)
from luna_bench._internal.usecases.benchmark import (
    AlgorithmRetrieveAsyncRetrivalDataUcImpl,
    AlgorithmRetrieveAsyncSolutionsUcImpl,
    AlgorithmRetrieveSyncSolutionsUcImpl,
    AlgorithmRunAsBackgroundTasksUcImpl,
)
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_add import AlgorithmAddUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_filter import AlgorithmFilterUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_remove import AlgorithmRemoveUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_run import AlgorithmRunUcImpl
from luna_bench._internal.usecases.benchmark.benchmark_create import BenchmarkCreateUcImpl
from luna_bench._internal.usecases.benchmark.benchmark_delete import BenchmarkDeleteUcImpl
from luna_bench._internal.usecases.benchmark.benchmark_load import BenchmarkLoadUcImpl
from luna_bench._internal.usecases.benchmark.benchmark_load_all import BenchmarkLoadAllUcImpl
from luna_bench._internal.usecases.benchmark.benchmark_remove_modelset import BenchmarkRemoveModelsetUcImpl
from luna_bench._internal.usecases.benchmark.benchmark_set_modelset import BenchmarkSetModelsetUcImpl
from luna_bench._internal.usecases.benchmark.feature.feature_add import FeatureAddUcImpl
from luna_bench._internal.usecases.benchmark.feature.feature_remove import FeatureRemoveUcImpl
from luna_bench._internal.usecases.benchmark.feature.feature_run import FeatureRunUcImpl
from luna_bench._internal.usecases.benchmark.metric.metric_add import MetricAddUcImpl
from luna_bench._internal.usecases.benchmark.metric.metric_remove import MetricRemoveUcImpl
from luna_bench._internal.usecases.benchmark.metric.metric_run import MetricRunUcImpl
from luna_bench._internal.usecases.benchmark.plot.plot_add import PlotAddUcImpl
from luna_bench._internal.usecases.benchmark.plot.plot_remove import PlotRemoveUcImpl
from luna_bench._internal.usecases.benchmark.plot.plot_run import PlotsRunUcImpl
from luna_bench._internal.usecases.benchmark.protocols import (
    AlgorithmAddUc,
    AlgorithmFilterUc,
    AlgorithmRemoveUc,
    AlgorithmRetrieveAsyncRetrivalDataUc,
    AlgorithmRetrieveAsyncSolutionsUc,
    AlgorithmRetrieveSyncSolutionsUc,
    AlgorithmRunAsBackgroundTasksUc,
    AlgorithmRunUc,
    BackgroundRetrieveAlgorithmAsyncUc,
    BackgroundRetrieveAlgorithmSyncUc,
    BackgroundRunAlgorithmAsyncUc,
    BackgroundRunAlgorithmSyncUc,
    BenchmarkCreateUc,
    BenchmarkDeleteUc,
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
from luna_bench._internal.usecases.modelset import (
    ModelAddUcImpl,
    ModelFetchUcImpl,
    ModelLoadAllUcImpl,
    ModelRemoveUcImpl,
    ModelSetCreateUcImpl,
    ModelSetDeleteUcImpl,
)
from luna_bench._internal.usecases.modelset.modelset_load import ModelSetLoadUcImpl
from luna_bench._internal.usecases.modelset.modelset_load_all import ModelSetLoadAllUcImpl
from luna_bench._internal.usecases.modelset.protocols import (
    ModelAddUc,
    ModelFetchUc,
    ModelLoadAllUc,
    ModelRemoveUc,
    ModelSetCreateUc,
    ModelSetDeleteUc,
    ModelSetLoadAllUc,
    ModelSetLoadUc,
)


class UsecaseContainer(containers.DeclarativeContainer):
    config: Configuration = providers.Configuration()

    dao_container = providers.Container(DaoContainer, config=config)
    mapper_container = providers.Container(MapperContainer)

    # ModelSet usecases
    modelset_create_uc: Provider[ModelSetCreateUc] = providers.Singleton(
        ModelSetCreateUcImpl, transaction=dao_container.transaction
    )
    modelset_load_uc: Provider[ModelSetLoadUc] = providers.Singleton(
        ModelSetLoadUcImpl, transaction=dao_container.transaction
    )
    modelset_load_all_uc: Provider[ModelSetLoadAllUc] = providers.Singleton(
        ModelSetLoadAllUcImpl, transaction=dao_container.transaction
    )
    modelset_delete_uc: Provider[ModelSetDeleteUc] = providers.Singleton(
        ModelSetDeleteUcImpl, transaction=dao_container.transaction
    )

    model_add_uc: Provider[ModelAddUc] = providers.Singleton(ModelAddUcImpl, transaction=dao_container.transaction)
    model_remove_uc: Provider[ModelRemoveUc] = providers.Singleton(
        ModelRemoveUcImpl, transaction=dao_container.transaction
    )
    model_load_all_uc: Provider[ModelLoadAllUc] = providers.Singleton(
        ModelLoadAllUcImpl, transaction=dao_container.transaction
    )

    model_fetch_uc: Provider[ModelFetchUc] = providers.Singleton(
        ModelFetchUcImpl, transaction=dao_container.transaction
    )

    # Benchmark usecases
    benchmark_create_uc: Provider[BenchmarkCreateUc] = providers.Singleton(
        BenchmarkCreateUcImpl,
        transaction=dao_container.transaction,
        benchmark_mapper=mapper_container.benchmark_mapper,
    )
    benchmark_delete_uc: Provider[BenchmarkDeleteUc] = providers.Singleton(
        BenchmarkDeleteUcImpl, transaction=dao_container.transaction
    )
    benchmark_load_uc: Provider[BenchmarkLoadUc] = providers.Singleton(
        BenchmarkLoadUcImpl,
        transaction=dao_container.transaction,
        benchmark_mapper=mapper_container.benchmark_mapper,
    )
    benchmark_load_all_uc: Provider[BenchmarkLoadAllUc] = providers.Singleton(
        BenchmarkLoadAllUcImpl,
        transaction=dao_container.transaction,
        benchmark_mapper=mapper_container.benchmark_mapper,
    )
    benchmark_add_metric_uc: Provider[MetricAddUc] = providers.Singleton(
        MetricAddUcImpl, transaction=dao_container.transaction
    )
    benchmark_add_feature_uc: Provider[FeatureAddUc] = providers.Singleton(
        FeatureAddUcImpl, transaction=dao_container.transaction
    )
    benchmark_add_plot_uc: Provider[PlotAddUc] = providers.Singleton(
        PlotAddUcImpl, transaction=dao_container.transaction
    )
    benchmark_add_algorithm_uc: Provider[AlgorithmAddUc] = providers.Singleton(
        AlgorithmAddUcImpl, transaction=dao_container.transaction
    )

    benchmark_remove_feature_uc: Provider[FeatureRemoveUc] = providers.Singleton(
        FeatureRemoveUcImpl, transaction=dao_container.transaction
    )
    benchmark_remove_metric_uc: Provider[MetricRemoveUc] = providers.Singleton(
        MetricRemoveUcImpl, transaction=dao_container.transaction
    )
    benchmark_remove_plot_uc: Provider[PlotRemoveUc] = providers.Singleton(
        PlotRemoveUcImpl, transaction=dao_container.transaction
    )

    benchmark_remove_algorithm_uc: Provider[AlgorithmRemoveUc] = providers.Singleton(
        AlgorithmRemoveUcImpl, transaction=dao_container.transaction
    )

    benchmark_set_modelset_uc: Provider[BenchmarkSetModelsetUc] = providers.Singleton(
        BenchmarkSetModelsetUcImpl, transaction=dao_container.transaction
    )

    benchmark_remove_modelset_uc: Provider[BenchmarkRemoveModelsetUc] = providers.Singleton(
        BenchmarkRemoveModelsetUcImpl, transaction=dao_container.transaction
    )

    benchmark_run_feature_uc: Provider[FeatureRunUc] = providers.Singleton(
        FeatureRunUcImpl, transaction=dao_container.transaction
    )

    benchmark_run_plots_uc: Provider[PlotsRunUc] = providers.Singleton(PlotsRunUcImpl)

    benchmark_algorithm_filter_uc: Provider[AlgorithmFilterUc] = providers.Singleton(AlgorithmFilterUcImpl)

    benchmark_background_run_algorithm_async_uc: Provider[BackgroundRunAlgorithmAsyncUc] = providers.Singleton(
        BackgroundRunAlgorithmAsyncUcImpl
    )

    benchmark_background_run_algorithm_sync_uc: Provider[BackgroundRunAlgorithmSyncUc] = providers.Singleton(
        BackgroundRunAlgorithmSyncUcImpl
    )

    benchmark_background_retrieve_algorithm_async_uc: Provider[BackgroundRetrieveAlgorithmAsyncUc] = (
        providers.Singleton(BackgroundRetrieveAlgorithmAsyncUcImpl)
    )

    benchmark_background_retrieve_algorithm_sync_uc: Provider[BackgroundRetrieveAlgorithmSyncUc] = providers.Singleton(
        BackgroundRetrieveAlgorithmSyncUcImpl
    )

    benchmark_algorithm_start_tasks_uc: Provider[AlgorithmRunAsBackgroundTasksUc] = providers.Singleton(
        AlgorithmRunAsBackgroundTasksUcImpl,
        transaction=dao_container.transaction,
        background_start_async=benchmark_background_run_algorithm_async_uc,
        background_start_sync=benchmark_background_run_algorithm_sync_uc,
    )

    benchmark_algorithm_retrieve_sync_uc: Provider[AlgorithmRetrieveSyncSolutionsUc] = providers.Singleton(
        AlgorithmRetrieveSyncSolutionsUcImpl,
        background_retrieve_sync=benchmark_background_retrieve_algorithm_sync_uc,
    )
    benchmark_algorithm_retrieve_async_retrieval_data_uc: Provider[AlgorithmRetrieveAsyncRetrivalDataUc] = (
        providers.Singleton(
            AlgorithmRetrieveAsyncRetrivalDataUcImpl,
            background_retrieve_async=benchmark_background_retrieve_algorithm_async_uc,
            transaction=dao_container.transaction,
        )
    )
    benchmark_algorithm_retrieve_async_solution_data_uc: Provider[AlgorithmRetrieveAsyncSolutionsUc] = (
        providers.Singleton(AlgorithmRetrieveAsyncSolutionsUcImpl, transaction=dao_container.transaction)
    )

    benchmark_run_algorithm_uc: Provider[AlgorithmRunUc] = providers.Singleton(
        AlgorithmRunUcImpl,
        algorithm_filter=benchmark_algorithm_filter_uc,
        retrieve_sync=benchmark_algorithm_retrieve_sync_uc,
        retrieve_async_retrieval_data=benchmark_algorithm_retrieve_async_retrieval_data_uc,
        retrieve_async_solution_data=benchmark_algorithm_retrieve_async_solution_data_uc,
        start_tasks=benchmark_algorithm_start_tasks_uc,
    )

    benchmark_run_metric_uc: Provider[MetricRunUc] = providers.Singleton(
        MetricRunUcImpl, transaction=dao_container.transaction
    )
