from peewee import AutoField, CharField

from luna_bench._internal.shared.database.base_model import BaseModel


class ModelSetTable(BaseModel):
    modelset_id = AutoField(primary_key=True)
    name = CharField(max_length=255)
