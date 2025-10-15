from peewee import AutoField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .feature_table import FeatureTable


class FeatureResultTable(BaseTable):
    id = AutoField(primary_key=True)

    feature = ForeignKeyField(
        FeatureTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    result_data = JSONField()  # type: ignore[no-untyped-call]
