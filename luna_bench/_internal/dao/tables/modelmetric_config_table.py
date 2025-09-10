from typing import TYPE_CHECKING

from peewee import AutoField, CharField, ForeignKeyField, ModelSelect
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .benchmark_table import BenchmarkTable
from ...domain_models import ModelmetricConfigDomain


class ModelmetricConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="modelmetrics",
        on_delete="CASCADE",
    )

    config_data = JSONField(
        json_dumps=lambda x: x.model_dump_json(),
        json_loads=lambda x: ModelmetricConfigDomain.ModelmetricConfig.model_validate_json(x),
    )

    if TYPE_CHECKING:
        from .modelmetric_result_table import ModelmetricResultTable

        result: ModelSelect[ModelmetricResultTable]

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
