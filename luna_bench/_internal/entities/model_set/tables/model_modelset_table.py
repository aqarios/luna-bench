from peewee import CompositeKey, ForeignKeyField

from luna_bench._internal.shared.database.base_model import BaseModel

from . import ModelMetadataTable
from .modelset_table import ModelSetTable


class ModelModelSetTable(BaseModel):
    model = ForeignKeyField(ModelMetadataTable, on_delete="CASCADE")
    model_set = ForeignKeyField(ModelSetTable, on_delete="CASCADE")

    class Meta:
        primary_key = CompositeKey("model", "model_set")
