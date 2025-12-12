from typing import TYPE_CHECKING, ClassVar

from peewee import AutoField, CharField, IntegerField, ModelSelect

from luna_bench._internal.dao.tables.base_table import BaseTable


class ModelMetadataTable(BaseTable):
    id: ClassVar[AutoField] = AutoField(primary_key=True)
    name = CharField(max_length=45, unique=True)
    hash = IntegerField(unique=True)

    if TYPE_CHECKING:
        modelsets: ModelSelect
