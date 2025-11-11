from typing import TYPE_CHECKING

from peewee import AutoField, CharField, ForeignKeyField, ModelSelect
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

from .benchmark_table import BenchmarkTable


class AlgorithmTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, collation="NOCASE")

    status: JobStatus = CharField(max_length=16, choices=[(s.value, s.name) for s in JobStatus])  # type: ignore[assignment]
    algorithm_type = CharField(max_length=16, choices=[(s.value, s.name) for s in AlgorithmType])

    registered_id = CharField(max_length=255)
    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="algorithms",
        on_delete="CASCADE",
    )

    config_data = JSONField(  # type: ignore[no-untyped-call]
        json_loads=lambda x: ArbitraryDataDomain.model_validate_json(x),
        json_dumps=lambda x: x.model_dump_json(),
    )
    if TYPE_CHECKING:
        results: ModelSelect

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
