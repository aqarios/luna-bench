from typing import TYPE_CHECKING

from peewee import AutoField, CharField, ForeignKeyField, IntegerField, ModelSelect
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

from .benchmark_table import BenchmarkTable

if TYPE_CHECKING:
    from luna_bench._internal.dao.tables.algorithm_result_table import AlgorithmResultTable


class AlgorithmTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, collation="NOCASE")

    algorithm_type = CharField(max_length=16, choices=[(s.value, s.name) for s in AlgorithmType])

    # How often the algorithm is run on every model of the benchmark. One by default,
    # which is what a database written before repetitions existed reads back as.
    repetitions = IntegerField(default=1)

    registered_id = CharField(max_length=255)
    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="algorithms",
        on_delete="CASCADE",
    )

    config_data = JSONField(
        json_loads=ArbitraryDataDomain.model_validate_json,
        json_dumps=lambda x: x.model_dump_json(),
    )
    if TYPE_CHECKING:
        results: ModelSelect[AlgorithmResultTable]

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
