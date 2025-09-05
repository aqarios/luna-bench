from peewee import AutoField, BlobField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .solve_job_config_table import SolveJobConfigTable


class SolveJobResultTable(BaseTable):
    id = AutoField(primary_key=True)

    solve_job = ForeignKeyField(
        SolveJobConfigTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    meta_data = JSONField()

    encoded_solution = BlobField()
