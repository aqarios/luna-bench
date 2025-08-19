from peewee import AutoField, CharField, ManyToManyField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.dao.tables.model_metadata_table import ModelMetadataTable


class ModelSetTable(BaseTable):
    id = AutoField(primary_key=True)
    name = CharField(max_length=255, unique=True, collation="NOCASE")

    models = ManyToManyField(ModelMetadataTable, backref="modelsets")
