from peewee import AutoField, BlobField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable

from .algorithm_config_table import AlgorithmConfigTable
from ...domain_models import AlgorithmResultDomain


class AlgorithmResultTable(BaseTable):
    id = AutoField(primary_key=True)

    algorithm = ForeignKeyField(
        AlgorithmConfigTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    meta_data = JSONField(
        json_dumps=lambda x: x.model_dump_json(),
        json_loads=lambda x: AlgorithmResultDomain.AlgorithmResultMetadata.model_validate_json(x),
        
    )

    encoded_solution = BlobField()
