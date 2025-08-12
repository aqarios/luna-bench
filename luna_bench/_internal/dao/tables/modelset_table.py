from peewee import AutoField, CharField, ManyToManyField
from pydantic import BaseModel

from luna_bench._internal.dao.tables import ModelMetadataTable


class ModelSetTable(BaseModel):
    id = AutoField(primary_key=True)
    name = CharField(max_length=255, unique=True, collation="NOCASE")

    models = ManyToManyField(ModelMetadataTable, backref="modelsets")
