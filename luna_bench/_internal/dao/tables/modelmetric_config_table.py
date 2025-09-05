from typing import TYPE_CHECKING

from peewee import AutoField, CharField, ForeignKeyField, ModelSelect
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .benchmark_table import BenchmarkTable


class ModelmetricConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="modelmetrics",
        on_delete="CASCADE",
    )

    config_data = JSONField()

    if TYPE_CHECKING:
        from .modelmetric_result_table import ModelmetricResultTable

        result: ModelSelect[ModelmetricResultTable]

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
