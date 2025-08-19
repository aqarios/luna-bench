from peewee import AutoField, CharField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .benchmark_table import BenchmarkTable


class MetricConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="metrics",
        on_delete="CASCADE",
    )

    config_data = JSONField()

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
