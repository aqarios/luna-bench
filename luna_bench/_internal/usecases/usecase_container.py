from dependency_injector import containers, providers
from dependency_injector.providers import Configuration, Provider

from luna_bench._internal.dao import DaoContainer
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_add import AlgorithmAddUcImpl
from luna_bench._internal.usecases.benchmark.algorithm.algorithm_remove import AlgorithmRemoveUcImpl
from luna_bench._internal.usecases.benchmark.feature.feature_remove import FeatureRemoveUcImpl
from luna_bench._internal.usecases.benchmark.plot.plot_add import PlotAddUcImpl
from luna_bench._internal.usecases.benchmark.plot.plot_remove import PlotRemoveUcImpl

from .benchmark import (
    BenchmarkRemoveModelsetUcImpl,
    BenchmarkSetModelsetUcImpl,
    FeatureAddUcImpl,
    MetricAddUcImpl,
    MetricRemoveUcImpl,
)
from .benchmark.benchmark_create import BenchmarkCreateUcImpl
from .benchmark.benchmark_delete import BenchmarkDeleteUcImpl
from .benchmark.benchmark_load import BenchmarkLoadUcImpl
from .benchmark.benchmark_load_all import BenchmarkLoadAllUcImpl
from .benchmark.protocols import (
    AlgorithmAddUc,
    AlgorithmRemoveUc,
    BenchmarkCreateUc,
    BenchmarkDeleteUc,
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
from .modelset import (
    ModelAddUcImpl,
    ModelFetchUcImpl,
    ModelLoadAllUcImpl,
    ModelRemoveUcImpl,
    ModelSetCreateUcImpl,
    ModelSetDeleteUcImpl,
)
from .modelset.modelset_load import ModelSetLoadUcImpl
from .modelset.modelset_load_all import ModelSetLoadAllUcImpl
from .modelset.protocols import (
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
        BenchmarkCreateUcImpl, transaction=dao_container.transaction
    )
    benchmark_delete_uc: Provider[BenchmarkDeleteUc] = providers.Singleton(
        BenchmarkDeleteUcImpl, transaction=dao_container.transaction
    )
    benchmark_load_uc: Provider[BenchmarkLoadUc] = providers.Singleton(
        BenchmarkLoadUcImpl, transaction=dao_container.transaction
    )
    benchmark_load_all_uc: Provider[BenchmarkLoadAllUc] = providers.Singleton(
        BenchmarkLoadAllUcImpl, transaction=dao_container.transaction
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
