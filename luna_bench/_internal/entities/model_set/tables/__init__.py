from luna_bench._internal.shared.database.base_model import database

from .metadata_table import ModelMetadataTable
from .model_table import ModelTable
from .modelset_table import ModelSetTable

__all__ = ["ModelMetadataTable", "ModelSetTable", "ModelTable"]


database.create_tables([
    ModelSetTable,
    ModelMetadataTable, 
    ModelTable, 
    ModelSetTable.models.get_through_model()

], safe=True)
