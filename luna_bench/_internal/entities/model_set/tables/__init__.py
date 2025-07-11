from luna_bench._internal.shared.database.base_model import database

from .metadata_table import ModelMetadataTable
from .model_modelset_table import ModelModelSetTable
from .model_table import ModelTable
from .modelset_table import ModelSetTable

__all__ = ["ModelMetadataTable", "ModelModelSetTable", "ModelSetTable", "ModelTable"]


database.create_tables([ModelSetTable, ModelMetadataTable, ModelTable, ModelModelSetTable], safe=True)
