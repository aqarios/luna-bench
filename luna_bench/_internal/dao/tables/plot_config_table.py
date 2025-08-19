from peewee import AutoField, CharField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables import BenchmarkTable
from luna_bench._internal.dao.tables.base_table import BaseTable


class PlotConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16, unique=True, collation="NOCASE")

    config_data = JSONField()

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="metric_models",
        on_delete="CASCADE",
    )

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
