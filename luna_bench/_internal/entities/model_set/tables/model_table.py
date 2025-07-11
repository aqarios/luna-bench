from peewee import BlobField, ForeignKeyField

from luna_bench._internal.shared.database.base_model import BaseModel

from .metadata_table import ModelMetadataTable


class ModelTable(BaseModel):
    # This id should always be the same as the one in modelmetadata -> we will insert it manually
    model_id = ForeignKeyField(ModelMetadataTable, backref="model", primary_key=True, on_delete="CASCADE")
    encoded_model = BlobField()
