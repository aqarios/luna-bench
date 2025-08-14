from peewee import AutoField, CharField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .benchmark_table import BenchmarkTable
from .metric_result_table import MetricResultTable


class MetricConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="metrics",
        on_delete="CASCADE",
    )

    result = ForeignKeyField(MetricResultTable, backref="metric_config", null=True, on_delete="SET NULL")

    config_data = JSONField()

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
