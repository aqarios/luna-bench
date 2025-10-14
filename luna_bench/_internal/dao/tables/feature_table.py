from typing import TYPE_CHECKING

from peewee import AutoField, CharField, ForeignKeyField, ModelSelect
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

from .benchmark_table import BenchmarkTable


class FeatureTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    registered_id = CharField(max_length=255)

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="features",
        on_delete="CASCADE",
    )

    config_data = JSONField(  # type: ignore[no-untyped-call]
        json_dumps=lambda x: x.model_dump_json(),
        json_loads=lambda x: ArbitraryDataDomain.model_validate_json(x),
    )

    if TYPE_CHECKING:
        result: ModelSelect

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
