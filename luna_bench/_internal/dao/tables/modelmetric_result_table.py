from peewee import AutoField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .modelmetric_config_table import ModelmetricConfigTable


class ModelmetricResultTable(BaseTable):
    id = AutoField(primary_key=True)

    config = ForeignKeyField(
        ModelmetricConfigTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    result_data = JSONField()
