from peewee import AutoField, BlobField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain

from .algorithm_table import AlgorithmTable


class AlgorithmResultTable(BaseTable):
    id = AutoField(primary_key=True)

    algorithm = ForeignKeyField(
        AlgorithmTable,
        backref="result",
        unique=True,
        on_delete="CASCADE",
    )

    meta_data = JSONField(  # type: ignore[no-untyped-call]
        json_dumps=lambda x: x.model_dump_json(),
        json_loads=lambda x: ArbitraryDataDomain.model_validate_json(x),
    )

    encoded_solution = BlobField()
