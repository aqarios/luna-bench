from peewee import BlobField, ForeignKeyField

from .base_table import BaseTable
from .model_metadata_table import ModelMetadataTable


class ModelTable(BaseTable):
    model_id = ForeignKeyField(ModelMetadataTable, backref="model", primary_key=True, on_delete="CASCADE")
    encoded_model = BlobField()
