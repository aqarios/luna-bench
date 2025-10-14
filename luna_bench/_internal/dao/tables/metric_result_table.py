from peewee import AutoField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.dao.tables.metric_table import MetricTable


class MetricResultTable(BaseTable):
    id = AutoField(primary_key=True)

    metric = ForeignKeyField(
        MetricTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    result_data = JSONField()  # type: ignore[no-untyped-call]
