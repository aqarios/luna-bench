from peewee import AutoField, CharField, ForeignKeyField

from luna_bench._internal.dao.tables import ModelSetTable
from luna_bench._internal.dao.tables.base_table import BaseTable


class BenchmarkTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    modelset = ForeignKeyField(ModelSetTable, backref="benchmarks", null=True, on_delete="SET NULL")
