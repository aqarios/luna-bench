from peewee import AutoField, BlobField, CharField, FixedCharField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

from luna_bench._internal.dao.tables.base_table import BaseTable
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.entities.enums.job_status_enum import JobStatus

from .algorithm_table import AlgorithmTable
from .model_metadata_table import ModelMetadataTable


class AlgorithmResultTable(BaseTable):
    id = AutoField(primary_key=True)

    status: JobStatus = CharField(max_length=16, choices=[(s.value, s.name) for s in JobStatus])  # type: ignore[assignment]
    error: str | None = CharField(max_length=255, null=True)  # type: ignore[assignment]

    encoded_solution: bytes | None = BlobField(null=True)  # type: ignore[assignment]

    meta_data: ArbitraryDataDomain | None = JSONField(  # type: ignore[no-untyped-call,assignment]
        json_loads=lambda x: ArbitraryDataDomain.model_validate_json(x),
        json_dumps=lambda x: x.model_dump_json(),
        null=True,
    )

    task_id: str | None = FixedCharField(max_length=36, null=True)  # type: ignore[assignment]
    retrival_data: ArbitraryDataDomain | None = JSONField(  # type: ignore[no-untyped-call,assignment]
        json_loads=lambda x: ArbitraryDataDomain.model_validate_json(x),
        json_dumps=lambda x: x.model_dump_json(),
        null=True,
    )
    algorithm = ForeignKeyField(AlgorithmTable, backref="results", on_delete="CASCADE")
    model_metadata = ForeignKeyField(ModelMetadataTable, backref="feature_results", on_delete="CASCADE")

    class Meta:
        indexes = ((("model_metadata", "algorithm"), True),)
