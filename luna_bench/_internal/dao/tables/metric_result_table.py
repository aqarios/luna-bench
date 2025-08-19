from peewee import AutoField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.dao.tables.metric_config_table import MetricConfigTable


class MetricResultTable(BaseTable):
    id = AutoField(primary_key=True)

    config = ForeignKeyField(
        MetricConfigTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    result_data = JSONField()
