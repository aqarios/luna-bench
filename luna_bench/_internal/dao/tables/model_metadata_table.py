from typing import ClassVar

from peewee import AutoField, CharField, IntegerField

from luna_bench._internal.dao.tables.base_table import BaseTable


class ModelMetadataTable(BaseTable):
    id: ClassVar[AutoField] = AutoField(primary_key=True)
    name = CharField(max_length=45)
    hash = IntegerField(unique=True)
