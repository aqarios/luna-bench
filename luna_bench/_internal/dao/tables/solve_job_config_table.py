from peewee import AutoField, CharField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .benchmark_table import Benchmark
from .solve_job_result_table import SolveJobResultTable


class SolveJobConfigTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True, collation="NOCASE")

    status = CharField(max_length=16)

    benchmark = ForeignKeyField(
        Benchmark,
        backref="solve_jobs",
        on_delete="CASCADE",
    )
    result = ForeignKeyField(SolveJobResultTable, backref="solve_job_config", null=True, on_delete="SET NULL")

    config_data = JSONField()

    class Meta:
        # Ensures uniqueness of name within each benchmark
        indexes = ((("benchmark", "name"), True),)
