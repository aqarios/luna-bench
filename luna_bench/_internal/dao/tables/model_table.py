from peewee import BlobField, ForeignKeyField

from luna_bench._internal.entities.database.base_model import BaseModel

from .metadata_table import ModelMetadataTable


class ModelTable(BaseModel):
    model_id = ForeignKeyField(ModelMetadataTable, backref="model", primary_key=True, on_delete="CASCADE")
    encoded_model = BlobField()
