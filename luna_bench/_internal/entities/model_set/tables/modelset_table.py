from peewee import AutoField, CharField, ManyToManyField

from luna_bench._internal.entities.model_set.tables import ModelMetadataTable
from luna_bench._internal.shared.database.base_model import BaseModel


class ModelSetTable(BaseModel):
    id = AutoField(primary_key=True)
    name = CharField(max_length=255)

    models = ManyToManyField(ModelMetadataTable, backref="modelsets")
