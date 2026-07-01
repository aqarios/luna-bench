from typing import TYPE_CHECKING

from peewee import AutoField, CharField, ForeignKeyField, ModelSelect

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.dao.tables.modelset_table import ModelSetTable

if TYPE_CHECKING:
    from luna_bench._internal.dao.tables.algorithm_table import AlgorithmTable
    from luna_bench._internal.dao.tables.feature_table import FeatureTable
    from luna_bench._internal.dao.tables.metric_table import MetricTable
    from luna_bench._internal.dao.tables.plot_config_table import PlotConfigTable


class BenchmarkTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    modelset = ForeignKeyField(ModelSetTable, backref="benchmarks", null=True, on_delete="SET NULL")

    if TYPE_CHECKING:
        # Backrefs

        features: ModelSelect[FeatureTable]
        algorithms: ModelSelect[AlgorithmTable]
        metrics: ModelSelect[MetricTable]
        plots: ModelSelect[PlotConfigTable]
