from peewee import AutoField, CharField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from ...domain_models import AlgorithmConfigDomain
from .benchmark_table import BenchmarkTable


class AlgorithmConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        BenchmarkTable,
        backref="solve_jobs",
        on_delete="CASCADE",
    )

    algorithm = JSONField(
        json_loads=lambda x: AlgorithmConfigDomain.Algorithm.model_validate_json(x),
        json_dumps=lambda x: x.model_dump_json(),
    )
    backend = JSONField(
        json_loads=lambda x: AlgorithmConfigDomain.Backend.model_validate_json(x) if x else None,
        json_dumps=lambda x: x.model_dump_json() if x else None,
        null=True,
    )

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
