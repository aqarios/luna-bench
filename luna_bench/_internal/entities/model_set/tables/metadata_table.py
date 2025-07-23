from peewee import AutoField, CharField, IntegerField

from luna_bench._internal.shared.database.base_model import BaseModel


class ModelMetadataTable(BaseModel):
    id = AutoField(primary_key=True)
    name = CharField(max_length=255)
    hash = IntegerField(unique=True)
