from dependency_injector import containers, providers
from dependency_injector.providers import Configuration, Provider

from luna_bench._internal.dao import StorageContainer

from .benchmark.benchmark_add_algorithm import BenchmarkAddAlgorithmUcImpl
from .benchmark.benchmark_add_metric import BenchmarkAddMetricUcImpl
from .benchmark.benchmark_add_modelmetric import BenchmarkAddModelMetricUcImpl
from .benchmark.benchmark_add_plot import BenchmarkAddPlotUcImpl
from .benchmark.benchmark_create import BenchmarkCreateUcImpl
from .benchmark.benchmark_delete import BenchmarkDeleteUcImpl
from .benchmark.benchmark_load import BenchmarkLoadUcImpl
from .benchmark.benchmark_load_all import BenchmarkLoadAllUcImpl
from .benchmark.benchmark_remove_algorithm import BenchmarkRemoveAlgorithmUcImpl
from .benchmark.benchmark_remove_metric import BenchmarkRemoveMetricUcImpl
from .benchmark.benchmark_remove_modelmetric import BenchmarkRemoveModelMetricUcImpl
from .benchmark.benchmark_remove_plot import BenchmarkRemovePlotUcImpl
from .benchmark.protocols import (
    BenchmarkAddAlgorithmUc,
    BenchmarkAddMetricUc,
    BenchmarkAddModelMetricUc,
    BenchmarkAddPlotUc,
    BenchmarkCreateUc,
    BenchmarkDeleteUc,
    BenchmarkLoadAllUc,
    BenchmarkLoadUc,
    BenchmarkRemoveAlgorithmUc,
    BenchmarkRemoveMetricUc,
    BenchmarkRemoveModelMetricUc,
    BenchmarkRemovePlotUc,
)
from .models import ModelAllUc, ModelAllUcImpl
from .models.model_fetch import ModelFetchUcImpl
from .models.protocols import ModelFetchUc
from .modelset import (
    ModelSetAddUc,
    ModelSetAddUcImpl,
    ModelSetCreateUc,
    ModelSetCreateUcImpl,
    ModelSetDeleteUc,
    ModelSetDeleteUcImpl,
    ModelSetRemoveUc,
    ModelSetRemoveUcImpl,
)
from .modelset.modelset_load import ModelSetLoadUcImpl
from .modelset.modelset_load_all import ModelSetLoadAllUcImpl
from .modelset.protocols import ModelSetLoadAllUc, ModelSetLoadUc


class UsecaseContainer(containers.DeclarativeContainer):
    config: Configuration = providers.Configuration()

    storage_container = providers.Container(StorageContainer, config=config)

    # ModelSet usecases
    modelset_create_uc: Provider[ModelSetCreateUc] = providers.Singleton(
        ModelSetCreateUcImpl, transaction=storage_container.transaction
    )
    modelset_load_uc: Provider[ModelSetLoadUc] = providers.Singleton(
        ModelSetLoadUcImpl, transaction=storage_container.transaction
    )
    modelset_load_all_uc: Provider[ModelSetLoadAllUc] = providers.Singleton(
        ModelSetLoadAllUcImpl, transaction=storage_container.transaction
    )

    modelset_add_uc: Provider[ModelSetAddUc] = providers.Singleton(
        ModelSetAddUcImpl, transaction=storage_container.transaction
    )
    modelset_remove_uc: Provider[ModelSetRemoveUc] = providers.Singleton(
        ModelSetRemoveUcImpl, transaction=storage_container.transaction
    )
    modelset_delete_uc: Provider[ModelSetDeleteUc] = providers.Singleton(
        ModelSetDeleteUcImpl, transaction=storage_container.transaction
    )

    # Model usecases
    model_all_uc: Provider[ModelAllUc] = providers.Singleton(ModelAllUcImpl, transaction=storage_container.transaction)

    model_fetch_uc: Provider[ModelFetchUc] = providers.Singleton(
        ModelFetchUcImpl, transaction=storage_container.transaction
    )

    # Benchmark usecases
    benchmark_create_uc: Provider[BenchmarkCreateUc] = providers.Singleton(
        BenchmarkCreateUcImpl, transaction=storage_container.transaction
    )
    benchmark_delete_uc: Provider[BenchmarkDeleteUc] = providers.Singleton(
        BenchmarkDeleteUcImpl, transaction=storage_container.transaction
    )
    benchmark_load_uc: Provider[BenchmarkLoadUc] = providers.Singleton(
        BenchmarkLoadUcImpl, transaction=storage_container.transaction
    )
    benchmark_load_all_uc: Provider[BenchmarkLoadAllUc] = providers.Singleton(
        BenchmarkLoadAllUcImpl, transaction=storage_container.transaction
    )
    benchmark_add_metric_uc: Provider[BenchmarkAddMetricUc] = providers.Singleton(
        BenchmarkAddMetricUcImpl, transaction=storage_container.transaction
    )
    benchmark_add_modelmetric_uc: Provider[BenchmarkAddModelMetricUc] = providers.Singleton(
        BenchmarkAddModelMetricUcImpl, transaction=storage_container.transaction
    )
    benchmark_add_plot_uc: Provider[BenchmarkAddPlotUc] = providers.Singleton(
        BenchmarkAddPlotUcImpl, transaction=storage_container.transaction
    )
    benchmark_add_algorithm_uc: Provider[BenchmarkAddAlgorithmUc] = providers.Singleton(
        BenchmarkAddAlgorithmUcImpl, transaction=storage_container.transaction
    )

    benchmark_remove_modelmetric_uc: Provider[BenchmarkRemoveModelMetricUc] = providers.Singleton(
        BenchmarkRemoveModelMetricUcImpl, transaction=storage_container.transaction
    )
    benchmark_remove_metric_uc: Provider[BenchmarkRemoveMetricUc] = providers.Singleton(
        BenchmarkRemoveMetricUcImpl, transaction=storage_container.transaction
    )
    benchmark_remove_plot_uc: Provider[BenchmarkRemovePlotUc] = providers.Singleton(
        BenchmarkRemovePlotUcImpl, transaction=storage_container.transaction
    )
    benchmark_remove_algorithm_uc: Provider[BenchmarkRemoveAlgorithmUc] = providers.Singleton(
        BenchmarkRemoveAlgorithmUcImpl, transaction=storage_container.transaction
    )
